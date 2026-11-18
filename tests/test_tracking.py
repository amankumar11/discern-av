from pathlib import Path

import mlflow

from discern.tracking import initialize_tracking


def test_local_tracking_initializes(monkeypatch, tmp_path: Path) -> None:
    tracking_directory = tmp_path / "mlruns"
    monkeypatch.setenv("MLFLOW_DIR", str(tracking_directory))
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)

    uri, experiment_id = initialize_tracking()

    assert uri == tracking_directory.resolve().as_uri()
    assert experiment_id
    assert mlflow.get_experiment(experiment_id) is not None
