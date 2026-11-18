import hashlib
from pathlib import Path

import pytest

from scripts.download_checkpoint import file_md5, validate


def test_artifact_validation_accepts_expected_file(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    payload = b"discern-av-stage0"
    artifact.write_bytes(payload)
    digest = hashlib.md5(payload, usedforsecurity=False).hexdigest()

    validate(artifact, len(payload), digest)


def test_artifact_validation_rejects_wrong_size(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"payload")

    with pytest.raises(ValueError, match="size mismatch"):
        validate(artifact, 1, file_md5(artifact))
