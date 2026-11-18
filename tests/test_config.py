from pathlib import Path

from discern.config import load_config, resolved_config


def test_default_config_resolves() -> None:
    config = resolved_config()

    assert config["project"]["stage"] == 0
    assert config["data"]["version"] == "v1.0-mini"
    assert config["model"]["frozen"] is True
    assert len(config["model"]["framework_revision"]) == 40


def test_hprc_runtime_override() -> None:
    config = load_config(["runtime=hprc", "+experiment=stage0_smoke"])

    assert config.runtime.device == "cuda"
    assert config.experiment.evaluate is True


def test_checkpoint_metadata_is_pinned() -> None:
    checkpoint = resolved_config()["model"]["checkpoint"]

    assert Path(checkpoint["path"]).suffix == ".pth"
    assert checkpoint["url"].startswith("https://download.openmmlab.com/")
    assert checkpoint["bytes"] > 0
    assert len(checkpoint["md5"]) == 32
