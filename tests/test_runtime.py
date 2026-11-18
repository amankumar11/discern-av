from discern.runtime import REQUIRED_DIRECTORIES, doctor_report, repository_root


def test_required_scaffold_exists() -> None:
    root = repository_root()

    assert all((root / directory).is_dir() for directory in REQUIRED_DIRECTORIES)


def test_doctor_is_machine_readable() -> None:
    report = doctor_report()

    assert report["ok"] is True
    assert report["missing_directories"] == []
    assert report["config_stage"] == 0
