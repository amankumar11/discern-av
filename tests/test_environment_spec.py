import subprocess

import yaml

from discern.runtime import repository_root


def test_conda_environment_pins_python() -> None:
    environment_path = repository_root() / "environment.yml"
    environment = yaml.safe_load(environment_path.read_text())

    assert environment["name"] == "discern-av"
    assert "python=3.10.15" in environment["dependencies"]


def test_container_pins_openmmlab_stack() -> None:
    root = repository_root()
    definition = (root / "containers" / "discern-av.def").read_text()
    constraints = (root / "containers" / "constraints.txt").read_text()

    assert "pytorch/pytorch:2.1.2-cuda11.8-cudnn8-devel" in definition
    assert "fe25f7a51d36e3702f961e198894580d83c4387b" in definition
    assert "mmcv==2.1.0" in constraints
    assert "mmdet==3.2.0" in constraints
    assert "mmengine==0.10.7" in constraints


def test_hpc_shell_scripts_parse() -> None:
    hpc_directory = repository_root() / "hpc"
    scripts = sorted(hpc_directory.glob("*.sh"))
    scripts.extend(sorted(hpc_directory.glob("*.sbatch")))

    result = subprocess.run(
        ["bash", "-n", *(str(path) for path in scripts)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
