# DISCERN-AV

DISCERN-AV is a runtime research layer for attributing multimodal perception
anomalies to nominal operation, benign degradation, or suspected adversarial
manipulation. The base camera-LiDAR detector remains frozen; radar is initially
used as an independent verification modality.

The full research design is in [PLAN.md](PLAN.md). This repository currently
contains the Stage 0 reproducibility scaffold and the locally tested Stage 1
manifest/cache implementation. Stage 1 acceptance still requires the logged
HPRC runs described in [docs/STAGE1.md](docs/STAGE1.md).

## Stage 0 quick start

The lightweight development environment runs configuration, tracking, lint,
and unit tests on a laptop. GPU perception dependencies are isolated in the
Apptainer image because MMCV and BEVFusion require Linux and CUDA.

```bash
conda env create -f environment.yml
conda activate discern-av
make check
python -m discern.cli doctor
python -m discern.cli init-tracking
```

If Conda is not installed, a Python 3.10 virtual environment with
`pip install -e '.[dev]'` provides the same laptop tooling.

## nuScenes mini (human step)

1. Register at [nuscenes.org](https://www.nuscenes.org/).
2. Download the nuScenes mini split.
3. Extract it so the selected root contains `v1.0-mini/`, `samples/`,
   `sweeps/`, and `maps/`.
4. On HPRC, set `NUSCENES_ROOT` to that directory. Dataset files are ignored
   by Git and should live on scratch storage.

## HPRC container and BEVFusion smoke run

The image uses the BEVFusion project integrated into MMDetection3D 1.4.0. The
source revision and the major CUDA/OpenMMLab dependencies are pinned in
`containers/discern-av.def` and `containers/constraints.txt`.

```bash
# On FASTER/ACES, or another rootless Linux build host:
module load WebProxy  # when building on an HPRC compute node
./hpc/build_container.sh

# Confirm the required values, then submit one GPU job:
export DISCERN_HPRC_ACCOUNT='<allocation>'
export NUSCENES_ROOT='/scratch/.../nuscenes'
./hpc/submit_stage0.sh
```

Grace runs Singularity on CentOS 7 and cannot build a definition file there.
Build on FASTER/ACES or an external x86-64 Linux host, then copy the resulting
SIF to Grace scratch. The scripts automatically select `apptainer` or
`singularity`, whichever is installed. Set `DISCERN_BUILD_FLAGS` if the build
host requires flags other than the default `--fakeroot`.

The job validates the dataset layout, downloads and verifies the official
OpenMMLab checkpoint, creates nuScenes mini info files when absent, imports the
compiled BEVFusion CUDA extensions, and runs MMDetection3D's test pipeline over
the mini validation split. Logs and evaluation metrics are written under
`artifacts/stage0/`.

Stage 0 is complete only after both `make check` and the HPRC GPU smoke job
pass. A laptop without NVIDIA CUDA cannot satisfy the second condition.

## Common commands

```bash
make test             # laptop unit tests
make lint             # Ruff lint and format check
make check            # both of the above
make config            # print the resolved Hydra configuration
make tracking          # initialize local MLflow tracking
```

Local MLflow data defaults to `./mlruns`. Set `MLFLOW_TRACKING_URI` to use a
different backend.

