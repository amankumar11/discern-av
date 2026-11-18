#!/usr/bin/env bash
#SBATCH --job-name=discern-s1-prep
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --partition=short
#SBATCH --time=02:00:00
#SBATCH --output=artifacts/stage1/prepare-%j.out

set -euo pipefail

: "${DISCERN_REPO:?DISCERN_REPO must point to the repository}"
: "${DISCERN_IMAGE:?DISCERN_IMAGE must point to the SIF image}"
: "${NUSCENES_ROOT:?NUSCENES_ROOT must point to full nuScenes trainval}"

if [[ -n "$(git -C "${DISCERN_REPO}" status --porcelain)" ]]; then
  echo "Refusing an uncommitted Stage 1 run; commit the repository first" >&2
  exit 1
fi
echo "source_commit=$(git -C "${DISCERN_REPO}" rev-parse HEAD)"

if command -v apptainer >/dev/null 2>&1; then
  container_runtime="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  container_runtime="singularity"
else
  echo "apptainer or singularity is required" >&2
  exit 1
fi

mkdir -p "${DISCERN_REPO}/artifacts/stage1"
"${container_runtime}" exec --cleanenv \
  --bind "${DISCERN_REPO}:/workspace" \
  --bind "${NUSCENES_ROOT}:/data/nuscenes" \
  --bind "${DISCERN_REPO}/artifacts:/artifacts" \
  --env PYTHONPATH=/workspace:/opt/mmdetection3d \
  "${DISCERN_IMAGE}" \
  python -m discern.data.prepare_nuscenes \
    --dataset-root /data/nuscenes \
    --version v1.0-trainval

"${container_runtime}" exec --cleanenv \
  --bind "${DISCERN_REPO}:/workspace" \
  --bind "${NUSCENES_ROOT}:/data/nuscenes" \
  --bind "${DISCERN_REPO}/artifacts:/artifacts" \
  --env PYTHONPATH=/workspace:/opt/mmdetection3d \
  "${DISCERN_IMAGE}" \
  python -m discern.data.build_manifest \
    --dataset-root /data/nuscenes \
    --output /artifacts/manifests/stage1 \
    --profile /artifacts/reports/data_profile.html
