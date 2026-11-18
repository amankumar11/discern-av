#!/usr/bin/env bash
#SBATCH --job-name=discern-s0
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu
#SBATCH --time=02:00:00
#SBATCH --output=artifacts/stage0/slurm-%j.out

set -euo pipefail

: "${DISCERN_REPO:?DISCERN_REPO must point to the repository}"
: "${DISCERN_IMAGE:?DISCERN_IMAGE must point to the Apptainer image}"
: "${NUSCENES_ROOT:?NUSCENES_ROOT must point to the extracted mini split}"

mkdir -p "${DISCERN_REPO}/artifacts/stage0"
if command -v apptainer >/dev/null 2>&1; then
  container_runtime="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  container_runtime="singularity"
else
  echo "apptainer or singularity is required on the compute node" >&2
  exit 1
fi

"${container_runtime}" exec --nv --cleanenv \
  --bind "${DISCERN_REPO}:/workspace" \
  --bind "${NUSCENES_ROOT}:/data/nuscenes" \
  --bind "${DISCERN_REPO}/artifacts:/artifacts" \
  --env DISCERN_ROOT=/workspace \
  --env DISCERN_ARTIFACTS=/artifacts \
  --env NUSCENES_ROOT=/data/nuscenes \
  --env "SLURM_JOB_ID=${SLURM_JOB_ID}" \
  --env "SLURM_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK}" \
  "${DISCERN_IMAGE}" \
  bash /workspace/hpc/bevfusion_smoke.sh

