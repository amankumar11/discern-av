"""Environment checks used by local development and cluster jobs."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

from discern.config import resolved_config

REQUIRED_DIRECTORIES = (
    "configs",
    "splits",
    "discern",
    "baselines",
    "hpc",
    "containers",
    "tests",
)


def repository_root() -> Path:
    """Return the repository root inferred from the installed source package."""
    return Path(__file__).resolve().parents[1]


def doctor_report() -> dict[str, Any]:
    """Build a machine-readable report without requiring GPU dependencies."""
    root = repository_root()
    missing = [name for name in REQUIRED_DIRECTORIES if not (root / name).is_dir()]
    config = resolved_config()
    return {
        "project_root": str(root),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "config_stage": config["project"]["stage"],
        "missing_directories": missing,
        "ok": not missing,
    }


def format_doctor_report() -> str:
    """Render the doctor report as stable, readable JSON."""
    return json.dumps(doctor_report(), indent=2, sort_keys=True)
