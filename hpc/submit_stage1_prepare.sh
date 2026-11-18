#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_path="${DISCERN_IMAGE:-${repo_root}/artifacts/containers/discern-av.sif}"
: "${DISCERN_HPRC_ACCOUNT:?Set DISCERN_HPRC_ACCOUNT to the HPRC allocation}"
: "${NUSCENES_ROOT:?Set NUSCENES_ROOT to full nuScenes trainval}"

if [[ ! -f "${image_path}" ]]; then
  echo "Container image not found: ${image_path}" >&2
  exit 1
fi
if [[ ! -d "${NUSCENES_ROOT}/v1.0-trainval" ]]; then
  echo "nuScenes trainval metadata not found under ${NUSCENES_ROOT}" >&2
  exit 1
fi

mkdir -p "${repo_root}/artifacts/stage1"
cd "${repo_root}"
sbatch \
  --account="${DISCERN_HPRC_ACCOUNT}" \
  --export="ALL,DISCERN_REPO=${repo_root},DISCERN_IMAGE=${image_path},NUSCENES_ROOT=${NUSCENES_ROOT}" \
  "${repo_root}/hpc/stage1_prepare.sbatch"
