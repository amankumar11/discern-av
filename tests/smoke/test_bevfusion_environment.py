import importlib.util

import pytest


@pytest.mark.gpu
@pytest.mark.integration
def test_bevfusion_cuda_extensions_are_importable() -> None:
    if importlib.util.find_spec("mmdet3d") is None:
        pytest.skip("MMDetection3D is only installed in the HPRC container")

    import torch
    from projects.BEVFusion.bevfusion.ops.bev_pool import bev_pool
    from projects.BEVFusion.bevfusion.ops.voxel import voxelization

    assert torch.cuda.is_available()
    assert callable(bev_pool)
    assert callable(voxelization)
