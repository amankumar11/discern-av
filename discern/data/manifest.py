"""Immutable, scene-grouped nuScenes manifests for Stage 1."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TABLE_FILENAMES = (
    "calibrated_sensor.json",
    "category.json",
    "ego_pose.json",
    "instance.json",
    "sample.json",
    "sample_annotation.json",
    "sample_data.json",
    "scene.json",
    "sensor.json",
)


class FrozenManifestError(RuntimeError):
    """Raised when an existing immutable manifest would be changed."""


@dataclass(frozen=True)
class ManifestBuildOptions:
    """Parameters that determine the Stage 1 split and frame manifest."""

    version: str
    train_scene_count: int = 100
    fit_scene_count: int = 50
    seed: int = 20261115
    expected_channels: tuple[str, ...] = (
        "CAM_BACK",
        "CAM_BACK_LEFT",
        "CAM_BACK_RIGHT",
        "CAM_FRONT",
        "CAM_FRONT_LEFT",
        "CAM_FRONT_RIGHT",
        "LIDAR_TOP",
        "RADAR_BACK_LEFT",
        "RADAR_BACK_RIGHT",
        "RADAR_FRONT",
        "RADAR_FRONT_LEFT",
        "RADAR_FRONT_RIGHT",
    )
    distance_bins_m: tuple[int, ...] = (0, 20, 40, 60)

    def __post_init__(self) -> None:
        if self.train_scene_count <= 0:
            raise ValueError("train_scene_count must be positive")
        if not 0 < self.fit_scene_count < self.train_scene_count:
            raise ValueError("fit_scene_count must split the selected train scenes")
        if not self.expected_channels:
            raise ValueError("expected_channels must not be empty")
        if tuple(sorted(set(self.distance_bins_m))) != self.distance_bins_m:
            raise ValueError("distance bins must be unique and increasing")
        if not self.distance_bins_m or self.distance_bins_m[0] != 0:
            raise ValueError("distance bins must begin at zero")


@dataclass(frozen=True)
class SceneAssignment:
    token: str
    name: str
    subset: str
    description: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class FrameRecord:
    sample_token: str
    scene_token: str
    scene_name: str
    subset: str
    timestamp: int
    sensor_files: dict[str, str]
    missing_channels: tuple[str, ...]
    object_counts: dict[str, int]
    distance_counts: dict[str, int]
    scene_tags: tuple[str, ...]


@dataclass(frozen=True)
class Stage1Manifest:
    schema_version: int
    dataset: str
    dataset_version: str
    options: ManifestBuildOptions
    source_fingerprints: dict[str, str]
    scenes: tuple[SceneAssignment, ...]
    frames: tuple[FrameRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical JSON-compatible representation."""
        return asdict(self)

    def content_hash(self) -> str:
        """Hash every split decision, source table, and frame record."""
        return _sha256_bytes(_canonical_json(self.to_dict()))

    def scenes_for(self, subset: str) -> tuple[SceneAssignment, ...]:
        return tuple(scene for scene in self.scenes if scene.subset == subset)


@dataclass(frozen=True)
class ManifestBundlePaths:
    summary_path: Path
    frames_path: Path
    split_path: Path


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_table(metadata_root: Path, filename: str) -> list[dict[str, Any]]:
    path = metadata_root / filename
    if not path.is_file():
        raise FileNotFoundError(f"missing nuScenes metadata table: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise TypeError(f"nuScenes table must contain a list: {path}")
    return value


def _index(rows: list[dict[str, Any]], key: str = "token") -> dict[str, dict]:
    return {str(row[key]): row for row in rows}


def _scene_tags(description: str) -> tuple[str, ...]:
    normalized = description.lower()
    tags = []
    if "night" in normalized:
        tags.append("night")
    if any(word in normalized for word in ("rain", "wet")):
        tags.append("rain")
    if not tags:
        tags.append("day-or-unspecified")
    return tuple(tags)


def _distance_label(distance: float, bins: tuple[int, ...]) -> str:
    for lower, upper in zip(bins, bins[1:], strict=True):
        if lower <= distance < upper:
            return f"{lower}-{upper}"
    return f"{bins[-1]}+"


def _select_train_scenes(
    rows: list[dict[str, Any]], options: ManifestBuildOptions
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(rows) < options.train_scene_count:
        raise ValueError(
            f"requested {options.train_scene_count} train scenes but found {len(rows)}"
        )

    def rank(scene: dict[str, Any]) -> str:
        value = f"{options.seed}:{scene['token']}".encode()
        return hashlib.sha256(value).hexdigest()

    selected = sorted(rows, key=rank)[: options.train_scene_count]
    return selected[: options.fit_scene_count], selected[options.fit_scene_count :]


def build_stage1_manifest(
    dataset_root: Path,
    split_scene_names: dict[str, list[str]],
    options: ManifestBuildOptions,
) -> Stage1Manifest:
    """Build deterministic fit, calibration, and validation frame records."""
    dataset_root = Path(dataset_root)
    metadata_root = dataset_root / options.version
    tables = {
        filename: _read_table(metadata_root, filename) for filename in TABLE_FILENAMES
    }
    fingerprints = {
        filename: _sha256_file(metadata_root / filename) for filename in TABLE_FILENAMES
    }

    train_names = set(split_scene_names.get("train", []))
    val_names = set(split_scene_names.get("val", []))
    overlap = train_names & val_names
    if overlap:
        raise ValueError(f"official train/validation scene overlap: {sorted(overlap)}")

    all_scenes = tables["scene.json"]
    scene_names_available = {str(scene["name"]) for scene in all_scenes}
    unknown = (train_names | val_names) - scene_names_available
    if unknown:
        raise ValueError(f"split refers to unknown scenes: {sorted(unknown)}")

    train_scenes = [scene for scene in all_scenes if scene["name"] in train_names]
    val_scenes = [scene for scene in all_scenes if scene["name"] in val_names]
    fit_scenes, calibration_scenes = _select_train_scenes(train_scenes, options)

    assignments: dict[str, SceneAssignment] = {}
    for subset, scenes in (
        ("fit", fit_scenes),
        ("calibration", calibration_scenes),
        ("validation", val_scenes),
    ):
        for scene in scenes:
            description = str(scene.get("description", ""))
            assignment = SceneAssignment(
                token=str(scene["token"]),
                name=str(scene["name"]),
                subset=subset,
                description=description,
                tags=_scene_tags(description),
            )
            if assignment.token in assignments:
                raise ValueError(f"scene assigned twice: {assignment.token}")
            assignments[assignment.token] = assignment

    sensors = _index(tables["sensor.json"])
    calibrated = _index(tables["calibrated_sensor.json"])
    ego_poses = _index(tables["ego_pose.json"])
    instances = _index(tables["instance.json"])
    categories = _index(tables["category.json"])

    sensor_files_by_sample: dict[str, dict[str, str]] = defaultdict(dict)
    ego_pose_by_sample: dict[str, list[float]] = {}
    for row in tables["sample_data.json"]:
        if row.get("is_key_frame", True) is False:
            continue
        calibration = calibrated[str(row["calibrated_sensor_token"])]
        sensor = sensors[str(calibration["sensor_token"])]
        channel = str(sensor["channel"])
        sample_token = str(row["sample_token"])
        filename = str(row["filename"])
        payload_path = Path(filename)
        if not payload_path.is_absolute():
            payload_path = dataset_root / payload_path
        if payload_path.is_file():
            sensor_files_by_sample[sample_token][channel] = filename
        if channel == "LIDAR_TOP":
            pose = ego_poses[str(row["ego_pose_token"])]
            ego_pose_by_sample[sample_token] = list(pose["translation"])

    annotations_by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for annotation in tables["sample_annotation.json"]:
        annotations_by_sample[str(annotation["sample_token"])].append(annotation)

    frames = []
    for sample in tables["sample.json"]:
        scene_token = str(sample["scene_token"])
        assignment = assignments.get(scene_token)
        if assignment is None:
            continue
        sample_token = str(sample["token"])
        sensor_files = dict(sorted(sensor_files_by_sample[sample_token].items()))
        missing = tuple(
            sorted(set(options.expected_channels) - set(sensor_files.keys()))
        )
        object_counts: Counter[str] = Counter()
        distance_counts: Counter[str] = Counter()
        ego_translation = ego_pose_by_sample.get(sample_token)
        for annotation in annotations_by_sample[sample_token]:
            instance = instances[str(annotation["instance_token"])]
            category = categories[str(instance["category_token"])]
            object_counts[str(category["name"])] += 1
            if ego_translation is not None:
                translation = annotation["translation"]
                distance = math.hypot(
                    float(translation[0]) - float(ego_translation[0]),
                    float(translation[1]) - float(ego_translation[1]),
                )
                distance_counts[_distance_label(distance, options.distance_bins_m)] += 1

        frames.append(
            FrameRecord(
                sample_token=sample_token,
                scene_token=scene_token,
                scene_name=assignment.name,
                subset=assignment.subset,
                timestamp=int(sample["timestamp"]),
                sensor_files=sensor_files,
                missing_channels=missing,
                object_counts=dict(sorted(object_counts.items())),
                distance_counts=dict(sorted(distance_counts.items())),
                scene_tags=assignment.tags,
            )
        )

    return Stage1Manifest(
        schema_version=1,
        dataset="nuScenes",
        dataset_version=options.version,
        options=options,
        source_fingerprints=dict(sorted(fingerprints.items())),
        scenes=tuple(sorted(assignments.values(), key=lambda item: item.token)),
        frames=tuple(
            sorted(frames, key=lambda item: (item.timestamp, item.sample_token))
        ),
    )


def _write_frozen(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise FrozenManifestError(f"refusing to change frozen manifest: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def write_manifest_bundle(
    manifest: Stage1Manifest, output_directory: Path
) -> ManifestBundlePaths:
    """Write a content-addressed manifest bundle without mutable overwrites."""
    output_directory = Path(output_directory)
    paths = ManifestBundlePaths(
        summary_path=output_directory / "manifest.json",
        frames_path=output_directory / "frames.jsonl",
        split_path=output_directory / "scene_split.json",
    )
    frames_content = b"".join(
        _canonical_json(asdict(frame)) + b"\n" for frame in manifest.frames
    )
    split_value = {
        "schema_version": manifest.schema_version,
        "dataset_version": manifest.dataset_version,
        "options": asdict(manifest.options),
        "scenes": [asdict(scene) for scene in manifest.scenes],
    }
    split_content = _canonical_json(split_value) + b"\n"
    summary_value = {
        "schema_version": manifest.schema_version,
        "dataset": manifest.dataset,
        "dataset_version": manifest.dataset_version,
        "manifest_hash": manifest.content_hash(),
        "scene_count": len(manifest.scenes),
        "frame_count": len(manifest.frames),
        "source_fingerprints": manifest.source_fingerprints,
        "files": {
            paths.frames_path.name: _sha256_bytes(frames_content),
            paths.split_path.name: _sha256_bytes(split_content),
        },
    }
    summary_content = _canonical_json(summary_value) + b"\n"

    _write_frozen(paths.frames_path, frames_content)
    _write_frozen(paths.split_path, split_content)
    _write_frozen(paths.summary_path, summary_content)
    return paths
