# Stage 1: data layer and frozen base detectors

Stage 1 is implemented in two layers. The laptop-safe layer builds deterministic
scene splits, immutable manifests, profiles, and cache contracts from nuScenes
metadata. The container layer runs frozen MMDetection3D models and writes their
outputs through those contracts.

Stage 0's container smoke test remains a prerequisite for accepting Stage 1.

## Manifest contract

The official nuScenes train and validation scene lists are loaded from the
pinned `nuscenes-devkit`. From the training scenes, 100 are selected by a stable
SHA-256 rank using the configured seed; 50 become `fit` and 50 become
`calibration`. Every official validation scene becomes `validation`. A scene can
appear in only one subset.

The manifest records source metadata hashes, sample tokens, timestamps, sensor
files, missing channels, object counts, distance bands, and scene tags. Files
are frozen: rerunning with identical inputs is idempotent, while an attempted
change fails instead of silently replacing the split.

## HPRC preparation

After full trainval and the Stage 0 SIF are present, set
`DISCERN_HPRC_ACCOUNT`, `DISCERN_IMAGE`, and `NUSCENES_ROOT`, then run
`hpc/submit_stage1_prepare.sh`. The submission helper validates the inputs and
creates the log directory before submitting `hpc/stage1_prepare.sbatch`. The job
creates train/validation info files without requiring the nuScenes test split,
then writes:

- `artifacts/manifests/stage1/manifest.json`
- `artifacts/manifests/stage1/scene_split.json`
- `artifacts/manifests/stage1/frames.jsonl`
- `artifacts/reports/data_profile.html`

`MODEL_CHECKPOINT` for cache jobs is a path on the HPRC host; the job mounts it
read-only at a stable container path. Set `MODEL_VARIANT` and `DATA_SUBSET`,
then use `hpc/submit_stage1_cache.sh` for each fused/LiDAR-only subset run.

## Base model cache

`discern.base.run_cache` forces evaluation mode, disables every gradient,
captures the camera BEV, LiDAR BEV, and raw dense heatmap using forward hooks,
and writes detections plus float16 CPU tensors to an immutable per-frame cache.
The cache identity includes the checkpoint, resolved model configuration, and
manifest SHA-256 hashes, plus the source commit. Each job also writes its fully
resolved configuration and `run_summary.json` below
`artifacts/work_dirs/stage1/`. Cache jobs reject a dirty source tree.

The fused and LiDAR-only variants use official MMDetection3D 1.4 configurations
and checkpoints. The camera-only baseline is intentionally blocked: the
published MIT checkpoint belongs to an archived MMCV 1.x stack and must not be
silently mixed with the pinned runtime. Stage 1 cannot be accepted until a
conversion or replacement baseline is approved and tested.

## Acceptance

Stage 1 is complete only after logged HPRC runs establish all of the following:

1. The fused validation result is within the tolerance stated in `PLAN.md`.
2. Every expected frame has a complete immutable cache entry.
3. The data profile was generated from the frozen manifest.
4. The camera-only baseline decision is resolved.
5. `RESULTS.md` records the run configuration, source commit, manifest hash,
   hardware, metrics, and cache index.
