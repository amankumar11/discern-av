"""Small command-line entry point for Stage 0 operations."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from discern.config import resolved_config
from discern.runtime import doctor_report, format_doctor_report
from discern.tracking import initialize_tracking


def build_parser() -> argparse.ArgumentParser:
    """Create the project command parser."""
    parser = argparse.ArgumentParser(prog="discern")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("config", help="print the resolved Hydra configuration")
    subparsers.add_parser("doctor", help="check the lightweight environment")
    subparsers.add_parser("init-tracking", help="initialize MLflow tracking")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a Stage 0 command."""
    args = build_parser().parse_args(argv)
    if args.command == "config":
        print(json.dumps(resolved_config(), indent=2, sort_keys=True))
        return 0
    if args.command == "doctor":
        report = doctor_report()
        print(format_doctor_report())
        return 0 if report["ok"] else 1
    if args.command == "init-tracking":
        uri, experiment_id = initialize_tracking()
        print(json.dumps({"experiment_id": experiment_id, "tracking_uri": uri}))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
