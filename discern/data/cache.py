"""Immutable per-frame cache storage for expensive base-model outputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class ImmutableCacheError(RuntimeError):
    """Raised when a cached frame would be overwritten with different data."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class CacheIdentity:
    model_name: str
    model_revision: str
    source_commit: str
    config_hash: str
    manifest_hash: str
    required_artifacts: tuple[str, ...]

    def run_hash(self) -> str:
        return _sha256(_canonical_json(asdict(self)))


class FrameCacheWriter:
    """Atomically writes one immutable directory per sample token."""

    def __init__(self, cache_root: Path, identity: CacheIdentity) -> None:
        self.identity = identity
        self.root = Path(cache_root) / identity.run_hash()
        self.frames_root = self.root / "frames"
        self.frames_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_name(value: str, label: str) -> None:
        if not SAFE_NAME.fullmatch(value):
            raise ValueError(f"unsafe {label}: {value!r}")

    def _record_value(
        self,
        sample_token: str,
        detections: dict[str, Any],
        artifacts: dict[str, bytes],
    ) -> tuple[dict[str, Any], bytes]:
        missing = set(self.identity.required_artifacts) - set(artifacts)
        if missing:
            raise ValueError(f"missing required artifacts: {sorted(missing)}")
        artifact_records = {}
        for name, payload in sorted(artifacts.items()):
            self._validate_name(name, "artifact name")
            artifact_records[name] = {
                "filename": f"{name}.bin",
                "sha256": _sha256(payload),
                "bytes": len(payload),
            }
        detections_content = _canonical_json(detections) + b"\n"
        record = {
            "schema_version": 1,
            "sample_token": sample_token,
            "cache_identity": asdict(self.identity),
            "detections": {
                "filename": "detections.json",
                "sha256": _sha256(detections_content),
                "bytes": len(detections_content),
            },
            "artifacts": artifact_records,
        }
        record["frame_hash"] = _sha256(_canonical_json(record))
        return record, detections_content

    def _verify_existing(
        self, frame_directory: Path, expected_record: dict[str, Any]
    ) -> bool:
        record_path = frame_directory / "record.json"
        if not record_path.is_file():
            return False
        actual = json.loads(record_path.read_text(encoding="utf-8"))
        if _canonical_json(actual) != _canonical_json(expected_record):
            return False
        for item in [actual["detections"], *actual["artifacts"].values()]:
            payload = (frame_directory / item["filename"]).read_bytes()
            if len(payload) != item["bytes"] or _sha256(payload) != item["sha256"]:
                return False
        return True

    def write_frame(
        self,
        sample_token: str,
        detections: dict[str, Any],
        artifacts: dict[str, bytes],
    ) -> Path:
        self._validate_name(sample_token, "sample token")
        record, detections_content = self._record_value(
            sample_token, detections, artifacts
        )
        destination = self.frames_root / sample_token
        if destination.exists():
            if self._verify_existing(destination, record):
                return destination
            raise ImmutableCacheError(
                f"refusing to overwrite different cache data: {destination}"
            )

        temporary = Path(
            tempfile.mkdtemp(prefix=f".{sample_token}.", dir=self.frames_root)
        )
        try:
            (temporary / "detections.json").write_bytes(detections_content)
            for name, payload in sorted(artifacts.items()):
                (temporary / f"{name}.bin").write_bytes(payload)
            (temporary / "record.json").write_bytes(_canonical_json(record) + b"\n")
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        return destination

    def finalize(self, expected_sample_tokens: tuple[str, ...]) -> Path:
        expected = tuple(sorted(set(expected_sample_tokens)))
        existing = {path.name for path in self.frames_root.iterdir() if path.is_dir()}
        missing = set(expected) - existing
        unexpected = existing - set(expected)
        if missing or unexpected:
            raise ValueError(
                f"cache coverage mismatch; missing={sorted(missing)}, "
                f"unexpected={sorted(unexpected)}"
            )
        frames = {}
        for token in expected:
            record = json.loads(
                (self.frames_root / token / "record.json").read_text(encoding="utf-8")
            )
            frames[token] = record["frame_hash"]
        index = {
            "schema_version": 1,
            "complete": True,
            "frame_count": len(expected),
            "cache_identity": asdict(self.identity),
            "frames": frames,
        }
        content = _canonical_json(index) + b"\n"
        index_path = self.root / "index.json"
        if index_path.exists() and index_path.read_bytes() != content:
            raise ImmutableCacheError(f"cache index is already frozen: {index_path}")
        if not index_path.exists():
            index_path.write_bytes(content)
        return index_path
