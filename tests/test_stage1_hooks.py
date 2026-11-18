from dataclasses import dataclass

import pytest

from discern.base.hooks import FeatureCapture, HookSpec, resolve_module


class FakeHandle:
    def __init__(self, module):
        self.module = module

    def remove(self) -> None:
        self.module.hook = None


class FakeModule:
    def __init__(self):
        self.hook = None

    def register_forward_hook(self, hook):
        self.hook = hook
        return FakeHandle(self)

    def emit(self, output) -> None:
        assert self.hook is not None
        self.hook(self, (), output)


@dataclass
class FakeModel:
    view_transform: FakeModule
    pts_middle_encoder: FakeModule


def test_feature_capture_registers_named_modules() -> None:
    model = FakeModel(FakeModule(), FakeModule())
    specs = (
        HookSpec("camera_bev", "view_transform"),
        HookSpec("lidar_bev", "pts_middle_encoder"),
    )

    with FeatureCapture(model, specs, serializer=lambda value: value) as capture:
        model.view_transform.emit(b"camera")
        model.pts_middle_encoder.emit(b"lidar")
        assert capture.snapshot() == {
            "camera_bev": b"camera",
            "lidar_bev": b"lidar",
        }

    assert model.view_transform.hook is None
    assert model.pts_middle_encoder.hook is None


def test_resolve_module_rejects_missing_path() -> None:
    model = FakeModel(FakeModule(), FakeModule())

    with pytest.raises(AttributeError, match="bbox_head"):
        resolve_module(model, "bbox_head.heatmap_head")
