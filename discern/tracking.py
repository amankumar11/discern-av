"""MLflow setup shared by experiments."""

from __future__ import annotations

from pathlib import Path

import mlflow

from discern.config import resolved_config


def initialize_tracking() -> tuple[str, str]:
    """Initialize the configured experiment and return its URI and ID."""
    config = resolved_config()
    tracking = config["tracking"]
    configured_uri = str(tracking["uri"]).strip()
    if configured_uri:
        uri = configured_uri
    else:
        directory = Path(str(tracking["directory"])).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        uri = directory.as_uri()

    mlflow.set_tracking_uri(uri)
    experiment = mlflow.set_experiment(str(tracking["experiment"]))
    return uri, experiment.experiment_id
