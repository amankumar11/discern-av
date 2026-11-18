# DISCERN-AV engineering rules

These rules apply to every implementation stage.

1. Never invent a number. Every reported result must come from a logged run
   with its resolved configuration, source commit, and data-manifest hash.
2. Base perception models stay frozen. Only code under `discern/` and the
   explicitly declared small heads may be trained.
3. Held-out attack and corruption types live in `splits/heldout.yaml`. Tests
   must reject a training or calibration manifest containing a held-out type.
4. Cache expensive detections, BEV features, and evidence tables. Downstream
   stages consume those immutable caches instead of rerunning backbones.
5. Write tests first for geometry, statistics, split integrity, and safety-
   relevant response code.
6. Add a short, evidence-backed entry to `RESULTS.md` for every completed
   stage. Do not manually transcribe experimental metrics.
7. Attack implementations are restricted to recorded data and simulation.
   This repository must not contain instructions for attacking real vehicles.
8. Keep the repository private until the invention-disclosure decision and
   dataset-license review are complete.

