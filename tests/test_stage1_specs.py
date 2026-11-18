from pathlib import Path

import pytest

from discern.base.specs import (
    ModelUnavailableError,
    camera_spec,
    fused_spec,
    lidar_spec,
)


def test_fused_and_lidar_specs_pin_expected_configs() -> None:
    framework = Path("/opt/mmdetection3d")
    fused = fused_spec(framework, Path("fused.pth"))
    lidar = lidar_spec(framework, Path("lidar.pth"))

    assert fused.available is True
    assert fused.config_path is not None
    assert "lidar-cam" in fused.config_path.name
    assert {hook.artifact_name for hook in fused.hooks} == {
        "camera_bev",
        "dense_heatmap",
        "lidar_bev",
    }
    assert lidar.available is True
    assert {hook.artifact_name for hook in lidar.hooks} == {
        "dense_heatmap",
        "lidar_bev",
    }


def test_camera_spec_fails_explicitly_instead_of_mixing_stacks() -> None:
    spec = camera_spec()

    with pytest.raises(ModelUnavailableError, match="archived MMCV 1.x"):
        spec.require_available()
