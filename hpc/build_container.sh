#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_path="${DISCERN_IMAGE:-${repo_root}/artifacts/containers/discern-av.sif}"

if command -v apptainer >/dev/null 2>&1; then
  container_runtime="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  container_runtime="singularity"
else
  echo "apptainer or singularity is required on the container build host" >&2
  exit 1
fi

mkdir -p "$(dirname "${image_path}")"
cd "${repo_root}"
read -r -a build_flags <<< "${DISCERN_BUILD_FLAGS:---fakeroot}"
"${container_runtime}" build "${build_flags[@]}" \
  "${image_path}" containers/discern-av.def
echo "Built ${image_path}"

