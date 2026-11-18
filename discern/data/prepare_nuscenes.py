"""Create MMDetection3D train/validation info files without requiring test data."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def _dataset_at_default_path(dataset_root: Path) -> Iterator[None]:
    """Expose nuScenes where MMDetection3D's v2 converter expects it."""
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="discern-nuscenes-convert-") as temporary:
        temporary_root = Path(temporary)
        alias = temporary_root / "data" / "nuscenes"
        alias.parent.mkdir(parents=True)
        alias.symlink_to(Path(dataset_root).resolve(), target_is_directory=True)
        os.chdir(temporary_root)
        try:
            yield
        finally:
            os.chdir(original_cwd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--version", default="v1.0-trainval")
    parser.add_argument("--prefix", default="nuscenes")
    parser.add_argument("--max-sweeps", type=int, default=10)
    return parser


def _is_v2_info(path: Path, loader) -> bool:
    if not path.is_file():
        return False
    try:
        value = loader(str(path))
    except Exception:
        return False
    return (
        isinstance(value, dict)
        and isinstance(value.get("metainfo"), dict)
        and isinstance(value.get("data_list"), list)
    )


def main() -> int:  # pragma: no cover - container-only data conversion
    args = build_parser().parse_args()
    train_path = args.dataset_root / f"{args.prefix}_infos_train.pkl"
    val_path = args.dataset_root / f"{args.prefix}_infos_val.pkl"
    try:
        from mmengine.fileio import load
        from mmengine.registry import init_default_scope
        from tools.dataset_converters import nuscenes_converter
        from tools.dataset_converters.update_infos_to_v2 import update_pkl_infos
    except ImportError as error:
        message = "Run nuScenes preparation inside the Stage 0 MMDetection3D image"
        raise RuntimeError(message) from error

    if _is_v2_info(train_path, load) and _is_v2_info(val_path, load):
        print(
            json.dumps(
                {"status": "existing", "train": str(train_path), "val": str(val_path)}
            )
        )
        return 0

    init_default_scope("mmdet3d")
    nuscenes_converter.create_nuscenes_infos(
        str(args.dataset_root),
        args.prefix,
        version=args.version,
        max_sweeps=args.max_sweeps,
    )
    # MMDetection3D 1.4's nuScenes v2 updater uses the hardcoded relative path
    # ``./data/nuscenes``. Scope that alias to this conversion rather than
    # requiring a repository-local dataset copy.
    with _dataset_at_default_path(args.dataset_root):
        update_pkl_infos(
            "nuscenes", out_dir=str(args.dataset_root), pkl_path=str(train_path)
        )
        update_pkl_infos(
            "nuscenes", out_dir=str(args.dataset_root), pkl_path=str(val_path)
        )
    print(
        json.dumps(
            {"status": "created", "train": str(train_path), "val": str(val_path)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
