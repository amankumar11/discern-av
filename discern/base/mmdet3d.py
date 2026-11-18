"""Lazy MMDetection3D adapter utilities for frozen Stage 1 inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from discern.base.specs import ModelSpec


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_model(model: Any) -> Any:
    """Put a base model in evaluation mode and disable every gradient."""
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model


def serialize_detection_sample(sample: Any) -> dict[str, Any]:
    """Convert one MMDet3D prediction into portable JSON primitives."""
    prediction = sample.pred_instances_3d
    boxes = prediction.bboxes_3d.tensor.detach().cpu().tolist()
    scores = prediction.scores_3d.detach().cpu().tolist()
    labels = prediction.labels_3d.detach().cpu().tolist()
    return {
        "sample_token": str(sample.metainfo["sample_idx"]),
        "boxes_3d": boxes,
        "scores_3d": scores,
        "labels_3d": labels,
    }


def config_hash(config_path: Path) -> str:
    """Hash the fully inherited MMEngine configuration."""
    try:
        from mmengine.config import Config
    except ImportError as error:  # pragma: no cover - container only
        raise RuntimeError("MMEngine is required to resolve model configs") from error
    config = Config.fromfile(str(config_path))
    encoded = json.dumps(config.to_dict(), sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def resolved_config_bytes(config: Any) -> bytes:
    """Serialize a fully resolved and runtime-patched MMEngine config."""
    value = config.to_dict() if hasattr(config, "to_dict") else config
    return (
        json.dumps(value, sort_keys=True, indent=2, default=str).encode("utf-8") + b"\n"
    )


class MMDet3DAdapter:
    """Build and freeze a pinned detector through an MMEngine Runner."""

    def __init__(self, spec: ModelSpec) -> None:
        spec.require_available()
        self.spec = spec

    def build_runner(self, work_directory: Path):
        try:
            from mmengine.config import Config
            from mmengine.runner import Runner
        except ImportError as error:  # pragma: no cover - container only
            message = "MMDetection3D container dependencies are missing"
            raise RuntimeError(message) from error
        assert self.spec.config_path is not None
        assert self.spec.checkpoint_path is not None
        config = Config.fromfile(str(self.spec.config_path))
        config.load_from = str(self.spec.checkpoint_path)
        config.work_dir = str(work_directory)
        runner = Runner.from_cfg(config)
        freeze_model(runner.model)
        return runner
