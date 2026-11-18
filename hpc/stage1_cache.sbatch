#!/usr/bin/env bash
#SBATCH --job-name=discern-s1-cache
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --gres=gpu:a100:1
#SBATCH --partition=gpu
#SBATCH --time=08:00:00
#SBATCH --output=artifacts/stage1/cache-%x-%j.out

set -euo pipefail

: "${DISCERN_REPO:?DISCERN_REPO must point to the repository}"
: "${DISCERN_IMAGE:?DISCERN_IMAGE must point to the SIF image}"
: "${NUSCENES_ROOT:?NUSCENES_ROOT must point to full nuScenes trainval}"
: "${MODEL_VARIANT:?MODEL_VARIANT must be fused or lidar_only}"
: "${MODEL_CHECKPOINT:?MODEL_CHECKPOINT must point to a checkpoint}"
: "${DATA_SUBSET:?DATA_SUBSET must be fit, calibration, or validation}"

if [[ ! -f "${MODEL_CHECKPOINT}" ]]; then
  echo "Checkpoint not found: ${MODEL_CHECKPOINT}" >&2
  exit 1
fi

if [[ -n "$(git -C "${DISCERN_REPO}" status --porcelain)" ]]; then
  echo "Refusing an uncommitted Stage 1 run; commit the repository first" >&2
  exit 1
fi
source_commit="$(git -C "${DISCERN_REPO}" rev-parse HEAD)"

if command -v apptainer >/dev/null 2>&1; then
  container_runtime="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  container_runtime="singularity"
else
  echo "apptainer or singularity is required" >&2
  exit 1
fi

work_directory="/artifacts/work_dirs/stage1/${MODEL_VARIANT}/${DATA_SUBSET}/${SLURM_JOB_ID}"
"${container_runtime}" exec --nv --cleanenv \
  --bind "${DISCERN_REPO}:/workspace" \
  --bind "${NUSCENES_ROOT}:/data/nuscenes" \
  --bind "${DISCERN_REPO}/artifacts:/artifacts" \
  --bind "${MODEL_CHECKPOINT}:/checkpoint/model.pth:ro" \
  --env PYTHONPATH=/workspace:/opt/mmdetection3d \
  "${DISCERN_IMAGE}" \
  python -m discern.base.run_cache \
    --variant "${MODEL_VARIANT}" \
    --checkpoint /checkpoint/model.pth \
    --dataset-root /data/nuscenes \
    --manifest-directory /artifacts/manifests/stage1 \
    --subset "${DATA_SUBSET}" \
    --cache-root /artifacts/cache/base \
    --work-directory "${work_directory}" \
    --source-commit "${source_commit}" \
    --workers "${SLURM_CPUS_PER_TASK}"
