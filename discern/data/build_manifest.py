"""Command-line builder for the frozen Stage 1 nuScenes manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from discern.data.manifest import (
    ManifestBuildOptions,
    build_stage1_manifest,
    write_manifest_bundle,
)
from discern.data.profile import write_data_profile


def official_split_names() -> dict[str, list[str]]:
    """Load official scene names from the pinned nuScenes devkit."""
    try:
        from nuscenes.utils.splits import create_splits_scenes
    except ImportError as error:
        raise RuntimeError(
            "nuscenes-devkit is required to load the official train/val splits"
        ) from error
    splits = create_splits_scenes()
    return {"train": list(splits["train"]), "val": list(splits["val"])}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--version", default="v1.0-trainval")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--train-scenes", type=int, default=100)
    parser.add_argument("--fit-scenes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261115)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    options = ManifestBuildOptions(
        version=args.version,
        train_scene_count=args.train_scenes,
        fit_scene_count=args.fit_scenes,
        seed=args.seed,
    )
    manifest = build_stage1_manifest(args.dataset_root, official_split_names(), options)
    paths = write_manifest_bundle(manifest, args.output)
    write_data_profile(manifest, args.profile)
    print(
        json.dumps(
            {
                "manifest_hash": manifest.content_hash(),
                "scene_count": len(manifest.scenes),
                "frame_count": len(manifest.frames),
                "summary": str(paths.summary_path),
                "profile": str(args.profile),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
