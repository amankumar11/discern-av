#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_path="${DISCERN_IMAGE:-${repo_root}/artifacts/containers/discern-av.sif}"
: "${DISCERN_HPRC_ACCOUNT:?Set DISCERN_HPRC_ACCOUNT to the HPRC allocation}"
: "${NUSCENES_ROOT:?Set NUSCENES_ROOT to the extracted nuScenes mini root}"

if [[ ! -f "${image_path}" ]]; then
  echo "Container image not found: ${image_path}" >&2
  exit 1
fi
if [[ ! -d "${NUSCENES_ROOT}/v1.0-mini" ]]; then
  echo "nuScenes mini metadata not found under ${NUSCENES_ROOT}" >&2
  exit 1
fi
if command -v apptainer >/dev/null 2>&1; then
  container_runtime="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  container_runtime="singularity"
else
  echo "apptainer or singularity is required on the submission host" >&2
  exit 1
fi

mkdir -p "${repo_root}/artifacts/stage0"
"${container_runtime}" exec \
  --bind "${repo_root}:/workspace" \
  --bind "${repo_root}/artifacts:/artifacts" \
  "${image_path}" \
  python /workspace/scripts/download_checkpoint.py \
    --url "https://download.openmmlab.com/mmdetection3d/v1.1.0_models/bevfusion/bevfusion_lidar-cam_voxel0075_second_secfpn_8xb4-cyclic-20e_nus-3d-5239b1af.pth" \
    --destination /artifacts/checkpoints/bevfusion_lidar-cam_nuscenes.pth \
    --bytes 167113973 \
    --md5 5873a41fa1ee29b4cdea346be177019a

cd "${repo_root}"
sbatch \
  --account="${DISCERN_HPRC_ACCOUNT}" \
  --export="ALL,DISCERN_REPO=${repo_root},DISCERN_IMAGE=${image_path},NUSCENES_ROOT=${NUSCENES_ROOT}" \
  "${repo_root}/hpc/stage0_bevfusion.sbatch"

