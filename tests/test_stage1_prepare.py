from pathlib import Path

from discern.data.prepare_nuscenes import _dataset_at_default_path, _is_v2_info


def test_converter_dataset_alias_is_scoped_and_restores_cwd(tmp_path: Path) -> None:
    dataset_root = tmp_path / "actual-nuscenes"
    dataset_root.mkdir()
    original_cwd = Path.cwd()

    with _dataset_at_default_path(dataset_root):
        alias = Path.cwd() / "data" / "nuscenes"
        assert alias.resolve() == dataset_root.resolve()

    assert Path.cwd() == original_cwd


def test_info_schema_check_rejects_legacy_file(tmp_path: Path) -> None:
    path = tmp_path / "infos.pkl"
    path.touch()

    assert _is_v2_info(path, lambda _path: {"infos": []}) is False
    assert _is_v2_info(path, lambda _path: {"metainfo": {}, "data_list": []}) is True
