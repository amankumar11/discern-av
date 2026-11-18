"""Framework-light feature hooks for frozen BEVFusion inference."""

from __future__ import annotations

import io
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HookSpec:
    artifact_name: str
    module_path: str


def resolve_module(model: Any, module_path: str) -> Any:
    """Resolve a dotted attribute path and produce a useful failure message."""
    current = model
    resolved = []
    for component in module_path.split("."):
        if not hasattr(current, component):
            prefix = ".".join(resolved) or type(model).__name__
            raise AttributeError(f"{prefix} has no module {component!r}")
        current = getattr(current, component)
        resolved.append(component)
    return current


class FeatureCapture:
    """Capture configured forward outputs and remove every hook on exit."""

    def __init__(
        self,
        model: Any,
        specs: tuple[HookSpec, ...],
        serializer: Callable[[Any], bytes],
    ) -> None:
        self.model = model
        self.specs = specs
        self.serializer = serializer
        self._handles: list[Any] = []
        self._captured: dict[str, bytes] = {}

    def __enter__(self) -> FeatureCapture:
        for spec in self.specs:
            module = resolve_module(self.model, spec.module_path)

            def capture(_module, _inputs, output, name=spec.artifact_name):
                payload = self.serializer(output)
                if not isinstance(payload, bytes):
                    raise TypeError("feature serializers must return bytes")
                self._captured[name] = payload

            self._handles.append(module.register_forward_hook(capture))
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        for handle in reversed(self._handles):
            handle.remove()
        self._handles.clear()

    def snapshot(self, clear: bool = False) -> dict[str, bytes]:
        value = dict(self._captured)
        if clear:
            self._captured.clear()
        return value


def torch_tensor_serializer(value: Any) -> bytes:
    """Serialize detached floating tensors as float16 CPU tensors."""
    try:
        import torch
    except ImportError as error:  # pragma: no cover - exercised in the container
        raise RuntimeError("PyTorch is required for tensor serialization") from error

    def prepare(item: Any) -> Any:
        if isinstance(item, torch.Tensor):
            tensor = item.detach().cpu()
            if tensor.is_floating_point():
                return tensor.to(dtype=torch.float16)
            return tensor
        if isinstance(item, dict):
            return {key: prepare(content) for key, content in item.items()}
        if isinstance(item, tuple):
            return tuple(prepare(content) for content in item)
        if isinstance(item, list):
            return [prepare(content) for content in item]
        return item

    stream = io.BytesIO()
    torch.save(prepare(value), stream)
    return stream.getvalue()


BEVFUSION_FUSED_HOOKS = (
    HookSpec("camera_bev", "view_transform"),
    HookSpec("lidar_bev", "pts_middle_encoder"),
    HookSpec("dense_heatmap", "bbox_head.heatmap_head"),
)

BEVFUSION_LIDAR_HOOKS = (
    HookSpec("lidar_bev", "pts_middle_encoder"),
    HookSpec("dense_heatmap", "bbox_head.heatmap_head"),
)
