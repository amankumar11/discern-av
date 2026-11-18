"""Pinned model specifications used by the Stage 1 adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from discern.base.hooks import (
    BEVFUSION_FUSED_HOOKS,
    BEVFUSION_LIDAR_HOOKS,
    HookSpec,
)


class ModelUnavailableError(RuntimeError):
    """Raised when a deliberately unsupported model variant is requested."""


@dataclass(frozen=True)
class ModelSpec:
    name: str
    variant: str
    config_path: Path | None
    checkpoint_path: Path | None
    hooks: tuple[HookSpec, ...]
    available: bool = True
    unavailable_reason: str | None = None

    def require_available(self) -> None:
        if not self.available:
            raise ModelUnavailableError(
                self.unavailable_reason or f"model is unavailable: {self.name}"
            )
        if self.config_path is None or self.checkpoint_path is None:
            raise ModelUnavailableError(f"model paths are incomplete: {self.name}")


def fused_spec(framework_root: Path, checkpoint: Path) -> ModelSpec:
    return ModelSpec(
        name="bevfusion-lidar-camera",
        variant="fused",
        config_path=framework_root / "projects/BEVFusion/configs/"
        "bevfusion_lidar-cam_voxel0075_second_secfpn_8xb4-cyclic-20e_nus-3d.py",
        checkpoint_path=checkpoint,
        hooks=BEVFUSION_FUSED_HOOKS,
    )


def lidar_spec(framework_root: Path, checkpoint: Path) -> ModelSpec:
    return ModelSpec(
        name="bevfusion-lidar",
        variant="lidar_only",
        config_path=framework_root / "projects/BEVFusion/configs/"
        "bevfusion_lidar_voxel0075_second_secfpn_8xb4-cyclic-20e_nus-3d.py",
        checkpoint_path=checkpoint,
        hooks=BEVFUSION_LIDAR_HOOKS,
    )


def camera_spec() -> ModelSpec:
    return ModelSpec(
        name="bevfusion-camera",
        variant="camera_only",
        config_path=None,
        checkpoint_path=None,
        hooks=(),
        available=False,
        unavailable_reason=(
            "The original MIT camera-only checkpoint targets the archived MMCV 1.x "
            "stack and is not compatible with the pinned MMDetection3D 1.4 runtime. "
            "A conversion or a replacement baseline must be approved before use."
        ),
    )
