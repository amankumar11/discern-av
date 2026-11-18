"""Hydra configuration helpers."""

from pathlib import Path
from typing import Any

from hydra import compose, initialize_config_dir
from omegaconf import DictConfig, OmegaConf


def config_directory() -> Path:
    """Return the repository's absolute Hydra configuration directory."""
    return Path(__file__).resolve().parents[1] / "configs"


def load_config(overrides: list[str] | None = None) -> DictConfig:
    """Compose the project configuration without changing the working directory."""
    with initialize_config_dir(version_base="1.3", config_dir=str(config_directory())):
        return compose(config_name="config", overrides=overrides or [])


def resolved_config(overrides: list[str] | None = None) -> dict[str, Any]:
    """Return the fully resolved configuration as plain Python containers."""
    config = load_config(overrides)
    result = OmegaConf.to_container(config, resolve=True)
    if not isinstance(result, dict):
        raise TypeError("The root project configuration must be a mapping")
    return result
