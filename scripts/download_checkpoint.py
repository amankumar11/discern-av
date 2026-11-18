"""Download a pinned artifact atomically and verify its size and MD5 digest."""

from __future__ import annotations

import argparse
import hashlib
import os
import urllib.request
from pathlib import Path


def file_md5(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the MD5 digest used by the upstream artifact server."""
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def validate(path: Path, expected_bytes: int, expected_md5: str) -> None:
    """Raise when an artifact does not match its pinned metadata."""
    actual_bytes = path.stat().st_size
    if actual_bytes != expected_bytes:
        message = f"size mismatch: expected {expected_bytes}, got {actual_bytes}"
        raise ValueError(message)
    actual_md5 = file_md5(path)
    if actual_md5.lower() != expected_md5.lower():
        raise ValueError(f"MD5 mismatch: expected {expected_md5}, got {actual_md5}")


def download(url: str, destination: Path, expected_bytes: int, md5: str) -> None:
    """Download to a temporary sibling and move it into place after validation."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        validate(destination, expected_bytes, md5)
        return

    temporary = destination.with_suffix(destination.suffix + f".part-{os.getpid()}")
    try:
        urllib.request.urlretrieve(url, temporary)
        validate(temporary, expected_bytes, md5)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """Parse command-line arguments and fetch the artifact."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--bytes", required=True, type=int, dest="expected_bytes")
    parser.add_argument("--md5", required=True)
    args = parser.parse_args()
    download(args.url, args.destination, args.expected_bytes, args.md5)
    print(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
