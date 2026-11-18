import json
from pathlib import Path

import pytest

from discern.data.manifest import (
    FrozenManifestError,
    ManifestBuildOptions,
    build_stage1_manifest,
    write_manifest_bundle,
)


def _build(root: Path, split_names: dict[str, list[str]]):
    options = ManifestBuildOptions(
        version="v1.0-test-fixture",
        train_scene_count=4,
        fit_scene_count=2,
        seed=20261115,
        expected_channels=("CAM_FRONT", "LIDAR_TOP"),
    )
    return build_stage1_manifest(root, split_names, options)


def test_manifest_is_scene_grouped_and_deterministic(nuscenes_fixture) -> None:
    root, split_names = nuscenes_fixture

    first = _build(root, split_names)
    second = _build(root, split_names)

    assert first.content_hash() == second.content_hash()
    assert len(first.frames) == 12
    assert len(first.scenes_for("fit")) == 2
    assert len(first.scenes_for("calibration")) == 2
    assert len(first.scenes_for("validation")) == 2

    subsets_by_scene: dict[str, set[str]] = {}
    for frame in first.frames:
        subsets_by_scene.setdefault(frame.scene_token, set()).add(frame.subset)
    assert all(len(subsets) == 1 for subsets in subsets_by_scene.values())


def test_manifest_records_missing_sensors_and_profile_fields(nuscenes_fixture) -> None:
    root, split_names = nuscenes_fixture

    manifest = _build(root, split_names)
    missing = [frame for frame in manifest.frames if frame.missing_channels]

    assert len(missing) == 1
    assert missing[0].missing_channels == ("CAM_FRONT",)
    assert missing[0].object_counts == {
        "human.pedestrian.adult": 1,
        "vehicle.car": 1,
    }
    assert missing[0].distance_counts == {"0-20": 1, "40-60": 1}
    assert set(missing[0].scene_tags) == {"night", "rain"}


def test_manifest_bundle_is_immutable(nuscenes_fixture, tmp_path: Path) -> None:
    root, split_names = nuscenes_fixture
    manifest = _build(root, split_names)
    output = tmp_path / "bundle"

    result = write_manifest_bundle(manifest, output)
    same_result = write_manifest_bundle(manifest, output)

    assert result == same_result
    assert result.summary_path.exists()
    assert result.frames_path.exists()
    assert result.split_path.exists()
    summary = json.loads(result.summary_path.read_text())
    assert summary["manifest_hash"] == manifest.content_hash()

    result.frames_path.write_text("changed", encoding="utf-8")
    with pytest.raises(FrozenManifestError):
        write_manifest_bundle(manifest, output)


def test_manifest_rejects_overlapping_official_splits(nuscenes_fixture) -> None:
    root, split_names = nuscenes_fixture
    split_names["val"].append(split_names["train"][0])

    with pytest.raises(ValueError, match="overlap"):
        _build(root, split_names)
