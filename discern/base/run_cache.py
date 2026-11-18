"""Run one frozen MMDetection3D branch and cache Stage 1 outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from discern.base.hooks import FeatureCapture, torch_tensor_serializer
from discern.base.mmdet3d import (
    freeze_model,
    resolved_config_bytes,
    serialize_detection_sample,
    sha256_file,
)
from discern.base.specs import camera_spec, fused_spec, lidar_spec
from discern.data.cache import CacheIdentity, FrameCacheWriter


def _load_manifest(
    manifest_directory: Path, subset: str
) -> tuple[str, tuple[str, ...]]:
    summary = json.loads((manifest_directory / "manifest.json").read_text())
    tokens = []
    with (manifest_directory / "frames.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            frame = json.loads(line)
            if frame["subset"] == subset:
                tokens.append(str(frame["sample_token"]))
    if not tokens:
        raise ValueError(f"manifest contains no frames for subset {subset!r}")
    return str(summary["manifest_hash"]), tuple(sorted(tokens))


def _info_indices(info_path: Path, tokens: tuple[str, ...]) -> list[int]:
    try:
        from mmengine.fileio import load
    except ImportError as error:  # pragma: no cover - container only
        message = "MMEngine is required to read nuScenes info files"
        raise RuntimeError(message) from error
    info = load(str(info_path))
    entries = info.get("data_list", info) if isinstance(info, dict) else info
    requested = set(tokens)
    indices = []
    found = set()
    for index, entry in enumerate(entries):
        token = entry.get("token", entry.get("sample_idx"))
        if token in requested:
            indices.append(index)
            found.add(token)
    missing = requested - found
    if missing:
        preview = sorted(missing)[:5]
        raise ValueError(f"nuScenes info file is missing manifest tokens: {preview}")
    return indices


def _model_spec(args):
    framework_root = Path(args.framework_root)
    checkpoint = Path(args.checkpoint)
    if args.variant == "fused":
        return fused_spec(framework_root, checkpoint)
    if args.variant == "lidar_only":
        return lidar_spec(framework_root, checkpoint)
    return camera_spec()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variant", choices=("fused", "lidar_only", "camera_only"), required=True
    )
    parser.add_argument("--framework-root", default="/opt/mmdetection3d")
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--manifest-directory", required=True, type=Path)
    parser.add_argument(
        "--subset", choices=("fit", "calibration", "validation"), required=True
    )
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--work-directory", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--workers", type=int, default=4)
    return parser


def main() -> int:  # pragma: no cover - exercised by the HPRC GPU job
    args = build_parser().parse_args()
    spec = _model_spec(args)
    spec.require_available()
    assert spec.config_path is not None
    assert spec.checkpoint_path is not None
    if not spec.checkpoint_path.is_file():
        raise FileNotFoundError(spec.checkpoint_path)

    try:
        from mmengine.config import Config
        from mmengine.evaluator import BaseMetric
        from mmengine.hooks import Hook
        from mmengine.runner import Runner
    except ImportError as error:
        message = "Run cache generation inside the Stage 0 container"
        raise RuntimeError(message) from error

    manifest_hash, expected_tokens = _load_manifest(
        args.manifest_directory, args.subset
    )
    info_name = (
        "nuscenes_infos_val.pkl"
        if args.subset == "validation"
        else "nuscenes_infos_train.pkl"
    )
    info_path = args.dataset_root / info_name
    indices = _info_indices(info_path, expected_tokens)

    class CacheOnlyMetric(BaseMetric):
        """Drive the test loop when a split has no official evaluator."""

        def process(self, data_batch: Any, data_samples: Any) -> None:
            return None

        def compute_metrics(self, results: list) -> dict:
            return {}

    cfg = Config.fromfile(str(spec.config_path))
    cfg.load_from = str(spec.checkpoint_path)
    cfg.work_dir = str(args.work_directory)
    if cfg.model.get("img_backbone") is not None:
        # The complete detector checkpoint already includes the image
        # backbone. Avoid an unnecessary network fetch of its initialization.
        cfg.model.img_backbone.init_cfg = None
    cfg.test_dataloader.batch_size = 1
    cfg.test_dataloader.num_workers = args.workers
    cfg.test_dataloader.persistent_workers = args.workers > 0
    cfg.test_dataloader.dataset.data_root = f"{args.dataset_root}/"
    cfg.test_dataloader.dataset.ann_file = info_name
    cfg.test_dataloader.dataset.indices = indices
    if args.subset == "validation":
        cfg.test_evaluator.data_root = f"{args.dataset_root}/"
        cfg.test_evaluator.ann_file = str(info_path)
    else:
        cfg.test_evaluator = dict(type=CacheOnlyMetric)

    resolved_config = resolved_config_bytes(cfg)
    resolved_config_hash = hashlib.sha256(resolved_config).hexdigest()
    args.work_directory.mkdir(parents=True, exist_ok=True)
    resolved_config_path = args.work_directory / "resolved_config.json"
    resolved_config_path.write_bytes(resolved_config)

    identity = CacheIdentity(
        model_name=spec.name,
        model_revision=sha256_file(spec.checkpoint_path),
        source_commit=args.source_commit,
        config_hash=resolved_config_hash,
        manifest_hash=manifest_hash,
        required_artifacts=tuple(hook.artifact_name for hook in spec.hooks),
    )
    writer = FrameCacheWriter(args.cache_root, identity)
    runner = Runner.from_cfg(cfg)
    freeze_model(runner.model)

    capture: FeatureCapture

    class CacheHook(Hook):
        priority = "LOWEST"

        def after_test_iter(
            self,
            runner,
            batch_idx: int,
            data_batch: Any = None,
            outputs: Any = None,
        ) -> None:
            if outputs is None or len(outputs) != 1:
                raise RuntimeError("Stage 1 caching requires test batch_size=1")
            detections = serialize_detection_sample(outputs[0])
            token = detections.pop("sample_token")
            artifacts = capture.snapshot(clear=True)
            writer.write_frame(token, detections, artifacts)

    with FeatureCapture(
        runner.model, spec.hooks, serializer=torch_tensor_serializer
    ) as capture:
        runner.register_hook(CacheHook())
        metrics = runner.test()

    index_path = writer.finalize(expected_tokens)
    summary = {
        "cache_index": str(index_path),
        "checkpoint_sha256": identity.model_revision,
        "manifest_hash": manifest_hash,
        "metrics": metrics,
        "model": spec.name,
        "resolved_config": str(resolved_config_path),
        "resolved_config_sha256": resolved_config_hash,
        "source_commit": args.source_commit,
        "subset": args.subset,
    }
    summary_path = args.work_directory / "run_summary.json"
    summary_path.write_text(
        json.dumps(summary, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({**summary, "run_summary": str(summary_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
