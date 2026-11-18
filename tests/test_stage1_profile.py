from pathlib import Path

from discern.data.manifest import ManifestBuildOptions, build_stage1_manifest
from discern.data.profile import write_data_profile


def test_profile_is_generated_from_manifest(nuscenes_fixture, tmp_path: Path) -> None:
    root, split_names = nuscenes_fixture
    manifest = build_stage1_manifest(
        root,
        split_names,
        ManifestBuildOptions(
            version="v1.0-test-fixture",
            train_scene_count=4,
            fit_scene_count=2,
            seed=20261115,
            expected_channels=("CAM_FRONT", "LIDAR_TOP"),
        ),
    )
    output = tmp_path / "data_profile.html"

    write_data_profile(manifest, output)

    html = output.read_text(encoding="utf-8")
    assert "DISCERN-AV Stage 1 data profile" in html
    assert "vehicle.car" in html
    assert "Missing sensor frames" in html
    assert manifest.content_hash() in html
