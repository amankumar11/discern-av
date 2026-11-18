#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_path="${DISCERN_IMAGE:-${repo_root}/artifacts/containers/discern-av.sif}"
: "${DISCERN_HPRC_ACCOUNT:?Set DISCERN_HPRC_ACCOUNT to the HPRC allocation}"
: "${NUSCENES_ROOT:?Set NUSCENES_ROOT to full nuScenes trainval}"
: "${MODEL_VARIANT:?Set MODEL_VARIANT to fused or lidar_only}"
: "${DATA_SUBSET:?Set DATA_SUBSET to fit, calibration, or validation}"

case "${MODEL_VARIANT}" in
  fused)
    default_checkpoint="${repo_root}/artifacts/checkpoints/bevfusion_lidar-cam_nuscenes.pth"
    ;;
  lidar_only)
    default_checkpoint="${repo_root}/artifacts/checkpoints/bevfusion_lidar_nuscenes.pth"
    ;;
  *)
    echo "MODEL_VARIANT must be fused or lidar_only" >&2
    exit 1
    ;;
esac

case "${DATA_SUBSET}" in
  fit|calibration|validation) ;;
  *)
    echo "DATA_SUBSET must be fit, calibration, or validation" >&2
    exit 1
    ;;
esac

checkpoint_path="${MODEL_CHECKPOINT:-${default_checkpoint}}"
if [[ ! -f "${image_path}" ]]; then
  echo "Container image not found: ${image_path}" >&2
  exit 1
fi
if [[ ! -f "${checkpoint_path}" ]]; then
  echo "Checkpoint not found: ${checkpoint_path}" >&2
  exit 1
fi
if [[ ! -f "${repo_root}/artifacts/manifests/stage1/manifest.json" ]]; then
  echo "Run submit_stage1_prepare.sh before cache jobs" >&2
  exit 1
fi

mkdir -p "${repo_root}/artifacts/stage1"
cd "${repo_root}"
sbatch \
  --account="${DISCERN_HPRC_ACCOUNT}" \
  --export="ALL,DISCERN_REPO=${repo_root},DISCERN_IMAGE=${image_path},NUSCENES_ROOT=${NUSCENES_ROOT},MODEL_VARIANT=${MODEL_VARIANT},MODEL_CHECKPOINT=${checkpoint_path},DATA_SUBSET=${DATA_SUBSET}" \
  "${repo_root}/hpc/stage1_cache.sbatch"
