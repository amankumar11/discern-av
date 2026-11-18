# DISCERN-AV results ledger

Results are appended only from logged runs. Each entry must identify the
resolved configuration, source commit, data-manifest hash, and output path.

## Stage 0 — Environment and scaffold

- Laptop validation (2026-11-18, current uncommitted Stage 0 worktree):
  `make check` passed with Ruff clean, 11 tests passed, and the CUDA-only
  integration test skipped as designed on macOS ARM. Log:
  `artifacts/stage0/local/check.log`.
- Hydra configuration composition and the environment doctor passed under
  Python 3.10.22. Resolved configuration and doctor output are stored under
  `artifacts/stage0/local/`.
- Local MLflow file tracking initialized successfully. Its initialization
  record is `artifacts/stage0/local/mlflow.json`.
- The official 167,113,973-byte OpenMMLab BEVFusion checkpoint downloaded and
  passed the pinned MD5 integrity check. It remains ignored by Git under
  `artifacts/checkpoints/`.
- HPRC Apptainer/Singularity SIF build: pending HPRC access.
- BEVFusion inference on nuScenes mini: pending dataset download and GPU job.

