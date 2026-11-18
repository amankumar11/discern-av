#!/usr/bin/env bash
set -euo pipefail

repo_root="${DISCERN_ROOT:-/workspace}"
mmdet3d_root="${MMDET3D_HOME:-/opt/mmdetection3d}"
data_root="${NUSCENES_ROOT:-/data/nuscenes}"
artifact_root="${DISCERN_ARTIFACTS:-/artifacts}"
checkpoint="${artifact_root}/checkpoints/bevfusion_lidar-cam_nuscenes.pth"
work_dir="${artifact_root}/stage0/${SLURM_JOB_ID:-manual}"
config="${mmdet3d_root}/projects/BEVFusion/configs/bevfusion_lidar-cam_voxel0075_second_secfpn_8xb4-cyclic-20e_nus-3d.py"

for required in v1.0-mini samples sweeps maps; do
  if [[ ! -e "${data_root}/${required}" ]]; then
    echo "Missing nuScenes mini entry: ${data_root}/${required}" >&2
    exit 1
  fi
done

mkdir -p "${work_dir}"
python "${repo_root}/scripts/download_checkpoint.py" \
  --url "https://download.openmmlab.com/mmdetection3d/v1.1.0_models/bevfusion/bevfusion_lidar-cam_voxel0075_second_secfpn_8xb4-cyclic-20e_nus-3d-5239b1af.pth" \
  --destination "${checkpoint}" \
  --bytes 167113973 \
  --md5 5873a41fa1ee29b4cdea346be177019a

cd "${mmdet3d_root}"
if [[ ! -f "${data_root}/nuscenes_infos_val.pkl" ]]; then
  python tools/create_data.py nuscenes \
    --root-path "${data_root}" \
    --out-dir "${data_root}" \
    --extra-tag nuscenes \
    --version v1.0-mini \
    --workers "${SLURM_CPUS_PER_TASK:-4}"
fi

python -c "import torch; assert torch.cuda.is_available(), 'CUDA is unavailable'"
python -c "from projects.BEVFusion.bevfusion.ops.bev_pool import bev_pool"
python -c "from projects.BEVFusion.bevfusion.ops.voxel import voxelization"
nvidia-smi

python tools/test.py "${config}" "${checkpoint}" \
  --work-dir "${work_dir}" \
  --cfg-options \
    "test_dataloader.dataset.data_root=${data_root}/" \
    "test_dataloader.dataset.ann_file=nuscenes_infos_val.pkl" \
    "test_dataloader.num_workers=${SLURM_CPUS_PER_TASK:-4}" \
    "test_evaluator.data_root=${data_root}/" \
    "test_evaluator.ann_file=${data_root}/nuscenes_infos_val.pkl"

python -m pip freeze | sort > "${work_dir}/environment.lock"
git -C "${repo_root}" rev-parse HEAD > "${work_dir}/source_commit.txt" 2>/dev/null || \
  echo "UNCOMMITTED" > "${work_dir}/source_commit.txt"
git -C "${repo_root}" status --short > "${work_dir}/source_status.txt"
echo "Stage 0 BEVFusion smoke run completed: ${work_dir}"

