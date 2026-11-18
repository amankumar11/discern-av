import json
from pathlib import Path

import pytest

from discern.data.cache import (
    CacheIdentity,
    FrameCacheWriter,
    ImmutableCacheError,
)


def _identity() -> CacheIdentity:
    return CacheIdentity(
        model_name="bevfusion-lidar-camera",
        model_revision="model-checkpoint-sha256",
        source_commit="source-commit-sha",
        config_hash="config-sha256",
        manifest_hash="manifest-sha256",
        required_artifacts=("camera_bev", "dense_heatmap", "lidar_bev"),
    )


def test_frame_cache_is_idempotent_and_immutable(tmp_path: Path) -> None:
    writer = FrameCacheWriter(tmp_path, _identity())
    detections = {"boxes_3d": [], "labels_3d": [], "scores_3d": []}
    artifacts = {
        "camera_bev": b"camera",
        "dense_heatmap": b"heatmap",
        "lidar_bev": b"lidar",
    }

    first = writer.write_frame("sample-token", detections, artifacts)
    second = writer.write_frame("sample-token", detections, artifacts)

    assert first == second
    record = json.loads((first / "record.json").read_text())
    assert set(record["artifacts"]) == set(artifacts)

    changed = dict(artifacts)
    changed["camera_bev"] = b"different"
    with pytest.raises(ImmutableCacheError):
        writer.write_frame("sample-token", detections, changed)


def test_cache_finalize_checks_coverage(tmp_path: Path) -> None:
    writer = FrameCacheWriter(tmp_path, _identity())
    detections = {"boxes_3d": [], "labels_3d": [], "scores_3d": []}
    artifacts = {
        "camera_bev": b"camera",
        "dense_heatmap": b"heatmap",
        "lidar_bev": b"lidar",
    }
    writer.write_frame("sample-one", detections, artifacts)

    with pytest.raises(ValueError, match="missing"):
        writer.finalize(("sample-one", "sample-two"))

    index_path = writer.finalize(("sample-one",))
    index = json.loads(index_path.read_text())
    assert index["complete"] is True
    assert index["frame_count"] == 1
    assert index["cache_identity"]["source_commit"] == "source-commit-sha"


def test_cache_rejects_unsafe_sample_token(tmp_path: Path) -> None:
    writer = FrameCacheWriter(tmp_path, _identity())

    with pytest.raises(ValueError, match="sample token"):
        writer.write_frame("../escape", {}, {})
