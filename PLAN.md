# Thesis Project Plan: Uncertainty- and Threat-Aware Multimodal Verification for AV Perception

Nov 15, 2026 · @Gurmehar

## 1. Summary

The recommended thesis is **DISCERN-AV: a runtime layer that tells benign sensor degradation apart from adversarial manipulation in a camera-LiDAR-radar perception stack, and responds differently to each.** Existing work measures uncertainty, or detects attacks, or benchmarks weather; none found attributes the cause and none bounds the rate of mistaking weather for an attack.

- **Refined title:** *Cause-Attributed Trust for Multimodal Perception: Separating Benign Degradation from Adversarial Manipulation with Risk-Budgeted Verification.* The original title still fits as a subtitle.
- **Novelty:** cause-attributed trust state; dual-envelope sequential tests with a false-alarm bound; counterfactual masking of one sensor in the fused feature map; verification effort allocated by driving risk.
- **Feasibility:** base detectors are pretrained and frozen. Only small heads are trained, so no large training run is needed.
- **Free stack:** nuScenes, MultiCorrupt, nuScenes-C, CARLA, BEVFusion on MMDetection3D, Depth Anything V2 Small, PyTorch. All free for academic use.
- **Results:** seven experiments; three of them (attribution, detection quality, cost) are enough for a defensible thesis.
- **Patent:** four candidate claims, with the closest prior art named. File an invention disclosure before any public release.
- **Build:** twelve stages written for Claude Code or Codex, with a go/no-go check at stage 3 that tests the core claim in week 3.

**Headline feature (added 15 Nov 2026): Witness.** Every flagged event becomes an incident capsule: a replay of the scene with the suspect sensor muted, a plain-language report locked to the measured evidence, and a tamper-evident log entry. It makes the system's reasoning visible in a demo and gives investigators a cause, not only a flag. Details are at the end of section 5; the build is stage 6b.

**Data science core (added 17 Nov 2026).** Under the autonomous-vehicle framing, most of the work in this thesis is data science: an evidence dataset built from raw sensor data, engineered features, a gradient-boosted classifier, conformal statistics with guarantees, and controlled experiments. The base detector is used frozen and never retrained. Section 5 now names that work and adds five pieces (DS1 to DS5): SHAP explanations, stricter statistics with a leakage audit, distribution-shift analysis, cost-sensitive thresholds, and a released evidence benchmark.

**Open question for the advisor:** whether the committee expects closed-loop simulation results, or accepts nuScenes results with CARLA as an extension. This decides whether stages 9 to 11 are required.

## 2. Problem statement and research questions

A fused camera-LiDAR-radar detector today cannot tell *why* it is unsure, and that is the problem this thesis attacks. Fog, a dirty lens, a miscalibrated sensor and a spoofed LiDAR return all show up as the same thing: lower confidence or cross-sensor disagreement. The right response to each is different.

- **Benign degradation** (weather, noise, dropout): keep the sensor, widen the uncertainty, slow down gracefully.
- **Adversarial manipulation** (spoofed points, adversarial patch, blinding): stop trusting the affected sensor region, verify the object by other means, and avoid both phantom braking and missed obstacles.

Treating an attack as weather leaves the attacker inside the fusion. Treating weather as an attack causes false quarantines and a vehicle that brakes for rain. Worse, a well-built adversarial input is often *confidently* wrong, so uncertainty alone does not flag it.

**Research questions**

1. **RQ1, attribution.** Can a runtime monitor separate nominal, benign-degraded and adversarial inputs per sensor and per object, with a bounded false-alarm rate?
2. **RQ2, response.** Does a cause-specific response (re-weight for degradation, quarantine for attack) beat uniform uncertainty-weighted fusion when both conditions occur?
3. **RQ3, cost.** Can verification effort be spent only where risk is high, so the whole system stays inside a real-time budget?
4. **RQ4, safety.** Does trust-calibrated perception output reduce closed-loop failures (collisions, phantom braking) in simulation?
5. **RQ5, limits.** How far does it hold against an adaptive attacker who keeps the sensors consistent with each other?

## 3. Prior work: what already exists

Every ingredient in the working title has been published separately; none of the work found joins them with cause attribution. The table groups the literature into seven threads and names what each leaves open. Search covered arXiv, security and vision venues, and USPTO up to November 2026.

| Thread | Representative work | What it does | What it leaves open |
| --- | --- | --- | --- |
| Uncertainty-aware fusion | [UMoE, ECAI 2023](https://arxiv.org/abs/2307.16121); [evidential fusion preprint, 2026](https://www.preprints.org/manuscript/202601.0488); [weather-aware Bayesian fusion, 2025](https://thesai.org/Downloads/Volume16No8/Paper_8-Autonomous_Driving_in_Adverse_Weather.pdf) | Feeds per-sensor uncertainty into fusion weights; UMoE tests under fog, adversarial noise and blinding | One scalar for every cause. UMoE itself shows weather and attacks both raise uncertainty, so the fusion cannot tell them apart |
| Conflict-aware fusion | [ECoLaF, WACV 2025](https://mlanthology.org/wacv/2025/deregnaucourt2025wacv-conflictguided); [ECFusion](https://arxiv.org/abs/2403.07372); [When Sensors Disagree, 2026](https://www.researchgate.net/publication/403025528_When_Sensors_Disagree_Conflict-Aware_Fusion_of_LiDAR_and_Camera_Streams_for_3D_Object_Detection_in_Adverse_Conditions) | Detects cross-modal disagreement and discounts the weaker sensor | Built for adverse conditions, not attackers. No security evaluation, no guarantee |
| Conformal perception | [MI-calibrated conformal fusion](https://arxiv.org/abs/2309.09593); [dual-threshold conformal abstention](https://arxiv.org/abs/2502.07255) | Distribution-free coverage and abstention for camera and LiDAR models | Guarantees assume exchangeable data. [Conformal sets degrade under attack](https://arxiv.org/abs/2405.08886) unless the model is adversarially trained |
| Attacks on fusion | [Fusion Is Not Enough, ICLR 2024](https://arxiv.org/abs/2304.14614); [LiDAR-only hiding attack on fusion](https://arxiv.org/abs/2312.01468); [frustum attack, USENIX Security 2022](https://www.usenix.org/system/files/sec22fall_hallyburton.pdf); [Cross-Modal Phantom, 2026](https://arxiv.org/abs/2604.21841) | Camera-only patches or a few LiDAR points defeat camera-LiDAR fusion; frustum and coordinated attacks stay consistent across sensors | Shows redundancy alone is not a defense. Supplies the adaptive attackers this thesis must test against |
| Physical-invariant defenses | [CARLO](https://arxiv.org/abs/2006.16974); [Shadow-Catcher](https://arxiv.org/abs/2008.12008); [ADoPT](https://arxiv.org/abs/2310.14504); LIFE (discussed in the frustum paper) | Check occlusion, free space, LiDAR shadows, temporal and camera-LiDAR consistency | Single attack class each, mostly LiDAR spoofing, KITTI. No benign-degradation control, so false alarms in fog or rain are unmeasured |
| Trust estimation | [MATE, CCS 2025](https://arxiv.org/abs/2503.04954) | Bayesian trust (Beta distributions, hidden Markov model) over agents and tracks, trust-weighted fusion | Multi-agent setting with insider agents. Not single-vehicle per-sensor trust, no weather-versus-attack split |
| Benchmarks | [MultiCorrupt](https://arxiv.org/abs/2402.11677); [Robo3D](https://ldkong.com/Robo3D); [nuScenes-C / KITTI-C](https://arxiv.org/abs/2303.11040); [MSC-Bench](https://arxiv.org/abs/2501.01037); [PSA-Fusion, WWW 2024](https://doi.org/10.1145/3589334.3645612); [Safety2Drive](https://arxiv.org/abs/2505.13872) | Corruption suites on nuScenes and KITTI; a physical-sensor-attack suite for fusion detectors; a CARLA suite with both | Corruptions and attacks are scored as accuracy drop. None scores whether a system *identifies which one it is facing* |

Two 2025-2026 systematization papers confirm the direction is open. A [2026 SoK on fusion attacks](https://arxiv.org/abs/2604.20621) reviews 48 attack studies and lists the absence of defenses that reason about inter-sensor consistency as a gap. An [end-to-end sensor-attack SoK](https://arxiv.org/abs/2509.11120) traces how sensor attacks propagate to planning, which supports closed-loop evaluation.

The closest neighbours, which the thesis must cite and beat or differ from:

- **[US 12,106,575](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12106575)** (granted patent): a verification unit decides whether a camera image change is a natural or an adversarial perturbation, using a supplementary sensor for plausibility. Camera-centric and rule-based; no calibrated guarantee, no per-object attribution across three modalities.
- **[Martingale monitors for shift cause, 2024](https://ar5iv.labs.arxiv.org/html/2407.21748)**: several martingale monitors used together to diagnose why a robot's inputs shifted. Same statistical tool, but no adversary and no multi-sensor fusion.
- **[AD2, 2026](https://arxiv.org/abs/2602.10160)**: closed-loop CARLA attack detector for end-to-end driving. Camera only, detects attacks but does not separate them from benign degradation.
- **[Selective sensor substitution, 2026](https://arxiv.org/abs/2604.12418)**: swaps a corrupted depth signal when cross-sensor inconsistency appears, treating malicious and natural causes identically.

## 4. The gap

No published system attributes a perception anomaly to its cause and then responds differently to each cause, with a stated error guarantee. Five specific holes follow from the survey.

1. **Uncertainty is treated as one number.** Fusion methods down-weight an uncertain sensor whether the cause is fog or a spoofer. Attackers who produce confident wrong outputs pass straight through.
2. **Security defenses ignore benign degradation.** CARLO, Shadow-Catcher and similar checks are evaluated on clean data plus one attack. Their false-alarm rate in rain, fog or sensor noise is unreported.
3. **Robustness benchmarks ignore the adversary, and attack benchmarks ignore weather.** No benchmark scores attribution, meaning whether the system knows which of the two it faces.
4. **Statistical guarantees break at exactly the wrong moment.** Conformal coverage assumes exchangeable data; an attack violates it. Nobody uses that violation itself as the detection signal for sensor trust in a fusion stack.
5. **Verification is all-or-nothing.** Checks run on every object every frame, or not at all. None spends effort in proportion to how much an object matters to the driving decision.

The working title already points at this gap. The plan below makes it concrete enough to build, measure and claim.

## 5. Proposed project and novelty

**Working name: DISCERN-AV** (Disambiguating Sensor Corruption from Exploits with Risk-budgeted verificatioN). It is a runtime layer that wraps an existing camera-LiDAR-radar detector, decides per sensor and per object whether an anomaly is benign or adversarial, and changes the fusion and the output accordingly.

The core scientific claim is one sentence: **benign degradation and attacks are separable because they leave different signatures in three measurable things at once: predictive uncertainty, physical consistency, and spatial structure.** Weather is global, smooth and physically lawful; it raises uncertainty everywhere. An attack is local, aligned to an object or to the ego path, often low-uncertainty, and breaks at least one physical invariant.

**Contributions**

1. **Cause-attributed trust state (main novelty).** Each sensor region and each object carries a posterior over three causes: nominal, benign-degraded, suspected-adversarial. Prior work carries a single confidence or trust scalar.
2. **Dual-envelope anytime-valid monitors.** Two sequential tests per sensor, built as conformal test martingales against fixed reference sets. One reference is clean data; the other is clean plus a pool of benign corruptions. Only the first firing means degradation. Both firing means the input lies outside everything benign, so it is flagged as suspected attack. The chance of ever falsely flagging an attack during in-envelope benign driving is bounded by a chosen level, for example 5%.
3. **Counterfactual modality ablation at BEV level.** For a suspicious object, the fusion head is re-run with one modality's features masked in that object's region. If the object exists only because of one sensor, and that sensor fails its physical checks, blame is assigned to it. Backbones are not re-run, so this is cheap.
4. **Risk-budgeted verification cascade.** Three tiers of checks of rising cost. Budget goes to objects by suspicion times criticality (inside the ego corridor, short time-to-collision). This is the adaptive part of the title.
5. **Cause-specific response and a trust-calibrated output contract.** Degraded: inflate variance and re-weight. Suspected attack: quarantine the sensor in that region and re-detect with the rest. Every object leaves perception labelled confirmed, cautious or rejected, with a calibrated existence probability.
6. **Attribution benchmark.** Paired clean, benign-corrupted and attacked versions of the same nuScenes frames and CARLA scenarios, with new metrics: attribution accuracy, false-quarantine rate under weather, detection delay, and trust calibration error. This is publishable on its own.

**Hypotheses to test (targets, not promises)**

| ID | Hypothesis | Target |
| --- | --- | --- |
| H1 | Attack versus benign is separable on attack and corruption types never seen in training | AUROC of 0.90 or higher; empirical false-quarantine rate at or under the 5% level |
| H2 | Cause-specific response beats uniform uncertainty weighting | Recover at least half of the mAP lost under attack, lose under 1 mAP on clean data |
| H3 | Risk budgeting keeps cost low | Mean added latency under 20% of the base detector |
| H4 | Trust-calibrated output improves closed-loop safety | Fewer collisions and fewer phantom hard-brakes than the base stack in CARLA |
| H5 | Consistency-preserving attacks are harder | Report the degradation honestly; show which tier still catches them |

A negative result on H5 is still a thesis result: it maps the limit of consistency-based defense.

### Headline feature: Witness, a perception black box that shows and tells

Witness turns every flagged event into an **incident capsule**: a replay of the scene with the suspect sensor muted, a plain-language report, and a tamper-evident log entry. It answers the question asked after every incident: what did the car see, and why did it distrust it?

**Why this feature: five current problems (as of November 2026)**

| Real-world problem | Evidence | What Witness adds |
| --- | --- | --- |
| Cars do not know when they cannot see | NHTSA's [EA26002](https://electrek.co/2026/03/19/nhtsa-upgrades-tesla-fsd-visibility-investigation-3-2-million-vehicles/), opened March 2026 over about 3.2 million Teslas, examines whether FSD's degradation detection missed glare, fog and dust before nine crashes | Each degraded-sensor verdict is logged with its evidence at the moment it is made |
| Unexplained braking erodes trust | NHTSA's phantom-braking probe [PE22002](https://driveteslacanada.ca/news/tesla-phantom-braking-investigation-closed-nhtsa/) ran four years over nearly 700,000 vehicles and closed in 2026 without a recall | A capsule states whether a trigger was attributed to degradation, attack or neither |
| Recorders log flags, not causes | The UN DSSAD recorder logs time-stamped flags such as ADS in control, collision detected and severe failure ([TRL summary](https://www.trl.co.uk/Uploads/TRL/Brochures/Regulatory%20preparation%20for%20ADS%20approval_Summary.pdf)) | A cause label plus evidence, in a form that can sit beside a DSSAD record |
| Language models in vehicles can be hijacked by text in the scene | [CHAI](https://www.theregister.com/2026/01/30/road_sign_hijack_ai/): printed signs redirected a GPT-4o driving agent in 81.8% of simulated trials | The narrator never touches control, and its report is locked to measured evidence |
| Driving-model explanations drift under sensor noise | [Lost in Fog](https://arxiv.org/abs/2605.21446): when a driving model's explanation changed under perturbation, trajectory error rose about 5.3 times | Explanations are verified against the evidence record before release |

**What a capsule contains**

1. **Muted-sensor replay.** Three synchronized views: what each sensor reported, what fusion believed, and the scene re-detected with the suspect modality masked. It reuses M3's counterfactual masking, so it needs no new model.
2. **Evidence overlay.** Per-object uncertainty, physical-consistency violations and monitor state drawn on the camera images and the LiDAR bird's-eye view.
3. **Evidence-locked report.** A frozen open vision-language model (Qwen3-VL) receives the structured evidence record and the image crops, and writes a short report as JSON claims. Every claim must cite a field of the record. A deterministic verifier checks each claim; a report that fails is replaced by a template. The cause label always comes from M3, never from the language model.
4. **Semantic note.** The model's own description of the crop, for example "flat printed image of a person on a vehicle side", kept in a separate field marked unverified.
5. **Hash-chained log.** Each capsule stores the SHA-256 hash of the previous one, so later edits are detectable.

**Live trust view.** A dashboard shows the bird's-eye scene with each object coloured by label (confirmed, cautious, rejected) and cause, during nuScenes replay and CARLA runs. This is the demo for the defense.

**Why it is research, not only a demo**

- Evidence locking is a testable claim. Measure ungrounded claims with and without the verifier, and attack the narrator with injected scene text (attack A8, section 7).
- The closest prior work is a [VehicleSec 2025 work-in-progress paper](https://www.usenix.org/conference/vehiclesec25/presentation/fernandez). It prompts language models over 40 text-encoded scenarios to separate benign sensor errors from attacks, and lists multimodal inputs as future work. [PhysNav-DG](https://arxiv.org/abs/2505.01881) pairs robot navigation with generated explanations.
- My searches found no system that locks explanations to a statistical attribution on real camera-LiDAR-radar data, or that tests the explainer against scene-text injection. Searches can miss work, so repeat this check before filing.
- The VehicleSec paper also bears on section 4: it is the nearest attempt at cause attribution. It works on text descriptions and gives no error-rate bound.

**Hypothesis H6 (proposed targets)**

| Measure | Target |
| --- | --- |
| Claims grounded before verification | ≥ 90% |
| Ungrounded claims in released reports | 0 in an audit of 200 capsules |
| Cause label changed by injected scene text, locked narrator | 0% (unlocked VLM-only narrator reported for contrast) |
| Semantic-note accuracy on crops with known attack type | Reported, no target |
| Report time per event on one A100 | Reported; off the control path |

**Limits.** Witness explains verdicts; it does not improve detection. If M3 is wrong, the report is faithfully wrong. The semantic note can hallucinate, which is why it is labelled unverified. The hash chain reveals edits after logging, not sensor spoofing before it. A capsule is not a certified event recorder.

### Data science core

The detector is off the shelf; what this thesis builds is a dataset, features, a classifier, statistical guarantees and an evaluation. This subsection names that work so the data science contribution is visible, then adds five pieces that make it explicit.

**What is already data science in the plan**

| Work | Where in the plan | Data science skill |
| --- | --- | --- |
| Evidence dataset: one row per object per condition, stored as parquet, with ground-truth cause labels | M1, stages 2 and 3 | Dataset design, labelling, data engineering |
| Uncertainty, physical-consistency and scene-context features | M1, stage 3 | Feature engineering |
| Attribution classifier (LightGBM) tested on held-out condition types | M3, stage 5 | Supervised learning, generalization testing |
| Conformal p-values, test martingales, conformal risk control | M2, M6, stages 4 and 6 | Statistical inference, sequential hypothesis testing |
| Temperature scaling of the attribution head | Stage 5 | Probability calibration |
| Baselines, ablations, seeds, bootstrap intervals, paired tests | Section 9 | Experimental design |
| Hydra, MLflow, DVC, Slurm job arrays | Stage 0 onward | MLOps and reproducibility |
| Witness reports and the committee console | Stages 6b and 13 | Data storytelling for non-experts |

**Five additions**

1. **DS1, explainable attribution (SHAP).** Compute TreeSHAP values for the LightGBM attribution head. Produce a global summary plot, the top features per cause class, and a per-event explanation that is written into the Witness evidence record as numbers M3 produced (so the narrator may cite them, and the verifier can check them). Use SHAP as a shortcut-learning check too: if the top features for "adversarial" are things that should not matter, such as object distance alone, frame index or scene identity, the classifier has learned an artefact of the dataset, not the physics.
2. **DS2, statistical rigour and leakage audit.** Section 9 already has seeds, bootstrap intervals and paired tests. Add: a scene-clustered bootstrap (frames in one scene are correlated, so resampling frames overstates precision); Holm-Bonferroni correction across the family of baseline comparisons; effect sizes next to every p-value; ECE, Brier score and reliability diagrams for M3. Leakage audit: every split is grouped by scene; the evidence table is validated against a schema; and a metadata-only classifier (scene, time of day, object class, distance, no evidence features) is trained alongside M3. If it comes close to M3's accuracy, cause labels are leaking through metadata and must be fixed before any result is reported. Visually check a random sample of 100 labelled rows for label errors.
3. **DS3, distribution-shift analysis.** For each held-out condition, measure how far its evidence distribution sits from the training distribution, using a domain classifier (the AUC of a model that tries to tell training rows from that condition's rows) and maximum mean discrepancy. Plot attribution accuracy and false-quarantine rate against that distance. This answers how far from its training data the system can go before it fails, and gives an empirical view of the "outside benign envelope" risk in section 12.
4. **DS4, cost-sensitive operating points.** A missed attack costs far more than wrongly marking a real object cautious in fog. Define a cost matrix as config values and choose decision thresholds by minimising expected cost, but only among operating points that keep the conformal false-alarm bound. The guarantee is never traded for cost. Because true costs are unknown, report expected-cost curves over a range of cost ratios (for example 10:1 to 1000:1 for missed attack against false quarantine) rather than a single number.
5. **DS5, released evidence benchmark.** Package the evidence table (features, cause labels, condition metadata; no raw sensor data) as **DISCERN-Evidence**, with a datasheet following [Datasheets for Datasets](https://arxiv.org/abs/1803.09010), a data card and a baseline notebook. A public benchmark is a citable contribution on its own and survives even if the stage 3 gate narrows the main claim. Because it is derived from nuScenes, it probably has to carry the same non-commercial share-alike terms; confirm with the nuScenes terms and the advisor, and release only after the disclosure decision in section 10.

**Hypothesis H7 (data science), proposed targets**

| Part | Claim | Proposed target |
| --- | --- | --- |
| H7a | Attribution relies on physics, not dataset artefacts | At least 3 of the top 5 SHAP features for the adversarial class are physical-consistency or counterfactual features |
| H7b | No label leakage through metadata | The metadata-only classifier stays at least 0.15 AUROC below M3 on held-out types |
| H7c | Degradation under shift is gradual | Reported as a curve of accuracy against shift distance, no target |
| H7d | Cost-aware thresholds help without breaking the guarantee | Lower expected cost than the default threshold across the cost-ratio range, with the empirical false-alarm rate still at or below the chosen level |

The targets are my proposals; set them with the advisor before running E9. Expected effort: about four to five working days spread over stages 1, 2, 3, 5, 6, 8, 12 and 13, all on CPU.

## 6. System architecture

DISCERN-AV is a wrapper, not a new detector: the base models stay frozen and pretrained, and only small heads are trained. This is what makes the project finishable on a student timeline and comparable against published baselines.

&#91;embedded content: DISCERN-AV architecture · 8 modules, M0 to M7, top to bottom\]

Data flows top to bottom. The attribution head (highlighted) is the new element: it turns evidence and monitor states into a cause, and the cause selects one of three responses.

| Module | What it does | How it is built |
| --- | --- | --- |
| M0 Base perception (frozen) | Fused detection plus single-modality branches | BEVFusion camera+LiDAR, its LiDAR-only and camera-only baselines, all with public nuScenes checkpoints. Radar is kept out of fusion and used as an independent witness |
| M1 Evidence extractors | Turns raw data and detections into evidence features | Three families, listed below |
| M2 Dual-envelope monitors | Sequential test per sensor stream (6 cameras, LiDAR, radar) | Conformal test martingales against two fixed reference sets, clean and clean-plus-benign |
| M3 Attribution head | Posterior over nominal, degraded, suspected-adversarial per object and per sensor region | Gradient-boosted trees or a small MLP on M1 features plus M2 states, temperature-scaled |
| M4 Risk scheduler | Chooses which objects get deeper checks | Criticality from ego corridor and time-to-collision, multiplied by suspicion, under a per-frame time budget |
| M5 Response and trust tracker | Applies the cause-specific action and remembers it | Variance inflation and re-weighting; BEV feature masking and re-detection; Beta-Bernoulli trust filter per track and per sensor region with forgetting |
| M6 Output contract | What the planner receives | Object list with calibrated existence probability, cause posterior, and a label: confirmed, cautious or rejected. Threshold set by conformal risk control so the in-corridor miss rate stays under a chosen bound on calibration data |

**M7 Witness (added).** M7 sits off the control path. It reads the evidence record that M1 to M6 produce for each flagged object and writes the incident capsule described in section 5. Nothing M7 outputs feeds back into detection or planning, so a failure or a hijack of the narrator cannot change what the vehicle does.

**Evidence families in M1**

- **Uncertainty (U).** Heatmap entropy and box variance from a few dropout passes through the detection head only, per modality branch.
- **Physical consistency (P).** Free-space ratio inside the box and LiDAR shadow behind it; point count against the count expected for that range and size; monocular depth against LiDAR depth inside the projected box; radar return present and radial velocity matching the track; track kinematics and sudden appearance; local high-frequency energy in the image region.
- **Scene context (S).** Global image contrast and brightness per camera, LiDAR return rate as a function of range, intensity histogram. These capture weather, which is global, so the head can learn that a local anomaly inside a globally normal scene is suspicious.

**Verification tiers**

| Tier | Runs on | Checks | Cost |
| --- | --- | --- | --- |
| 0 | Every object, every frame | U features, scene context, martingale update, branch agreement in BEV | Negligible; reuses base outputs |
| 1 | Objects flagged by Tier 0 or inside the ego corridor | Geometric P checks: free space, shadow, density, depth residual, radar | Milliseconds per object, CPU or light GPU |
| 2 | Flagged objects with high criticality | Counterfactual modality ablation, multi-frame re-verification over the track | One extra fusion-head pass per object region |

## 7. Threat model, attack suite and degradation suite

The attacker is outside the vehicle and manipulates what sensors receive; the compute stack, weights and vehicle network are assumed intact. All attacks are simulated on recorded data or in the simulator, following published attack models. No physical attack hardware and no real vehicle is involved.

**Attacker tiers**

- **T1, single-sensor.** Affects one modality. Black-box for spoofing, white-box for patches as a worst case.
- **T2, coordinated.** Affects camera and LiDAR together and keeps them mutually consistent.
- **T3, defense-aware.** Knows DISCERN-AV and optimizes to keep its evidence scores low.

Out of scope: GNSS and map attacks, V2X, compromised firmware, training-data poisoning.

**Attack suite**

| ID | Attack | Sensor | Modelled on | Role |
| --- | --- | --- | --- | --- |
| A1 | Ghost object injection: a small cluster of spoofed points near the ego path | LiDAR | [CARLO threat model](https://arxiv.org/abs/2006.16974) | Train |
| A2 | Object hiding: point removal in a region, or a few adversarial points above a car | LiDAR | [LiDAR-only hiding attack](https://arxiv.org/abs/2312.01468) | Held out |
| A3 | Adversarial patch on an object or the road, optimized against the fusion model | Camera | [Fusion Is Not Enough](https://arxiv.org/abs/2304.14614) | Train |
| A4 | Blinding and strong-light interference | Camera | [PSA-Fusion](https://doi.org/10.1145/3589334.3645612) | Held out |
| A5 | Frustum attack: spoofed points placed inside an existing object's camera frustum | LiDAR | [Frustum attack](https://www.usenix.org/system/files/sec22fall_hallyburton.pdf) | Held out, T2-style |
| A6 | Coordinated phantom in camera and LiDAR | Both | [Cross-Modal Phantom](https://arxiv.org/abs/2604.21841) | Held out, T2 |
| A7 | Defense-aware variant of A1 and A3 with the monitor score added to the attack loss | Either | This thesis | Held out, T3 |

**A8, narrator hijack (added, targets M7 only).** Text rendered into the camera images on signs or vehicle sides, in the style of CHAI, instructs the narrator to report the scene as clean or to blame weather. It tests the report, not the detector.

**Benign degradation suite**

| Source | Content | Role |
| --- | --- | --- |
| [MultiCorrupt](https://arxiv.org/abs/2402.11677) | Ten synthetic corruption types on nuScenes hitting LiDAR, cameras or both, including fog, snow and sensor misalignment, at graded severity | Split by type: some train, some held out |
| [nuScenes-C](https://arxiv.org/abs/2303.11040) | 27 corruption types covering weather, sensor noise and more | Held-out types only |
| nuScenes rain and night scenes | Real adverse conditions already in the dataset | Real-data check for false quarantines |
| CARLA weather presets | Fog, rain, low sun, night in simulation | Closed-loop benign condition |

**Split rule.** The attribution head never sees a held-out attack or a held-out corruption type during training or calibration. Results are reported leave-one-type-out, so the headline number measures generalization, not memorization.

## 8. Datasets, simulator and tech stack

Everything below is free to download and use for academic research. One licence point matters for the patent and any later startup: nuScenes and KITTI are non-commercial, while CARLA is not. A patent on the method is unaffected, but a commercial product could not ship weights trained on nuScenes without a commercial licence from its owner.

**Data and simulation**

| Resource | Use here | Licence and access |
| --- | --- | --- |
| [nuScenes](https://arxiv.org/abs/2512.02448) | Main dataset: 6 cameras, 1 LiDAR, 5 radars, 1,000 scenes of 20 s. Validation split for all headline results; a slice of train for fitting heads and calibration | CC BY-NC-SA 4.0. Free for academics after registering at nuscenes.org. Start with the mini split, then the full set on HPRC scratch |
| [MultiCorrupt](https://arxiv.org/abs/2402.11677) | Benign corruptions on nuScenes | Open-source generation code; data is produced locally from nuScenes |
| [nuScenes-C / KITTI-C toolkit](https://arxiv.org/abs/2303.11040) | Held-out benign corruptions | Open-source code; inherits the base dataset licence |
| [PSA-Fusion](https://doi.org/10.1145/3589334.3645612) | Reference implementations of physical sensor attacks on fusion detectors | Code released by the authors on GitHub; check its licence file before reuse |
| KITTI (optional) | Cross-dataset check and direct comparison with CARLO and Shadow-Catcher, which report on KITTI | CC BY-NC-SA 3.0, free registration |
| [CARLA 0.9.16](https://carla.readthedocs.io/en/0.9.16/download/) | Closed-loop evaluation with camera, LiDAR and radar sensors, scripted weather and injected attacks | Code MIT, assets CC-BY. Prebuilt Linux packages and Docker images. The UE4 line (0.9.x) is lighter than the UE5 line, which asks for 16 GB of GPU memory |

**Models (all pretrained, frozen)**

| Model | Role | Licence |
| --- | --- | --- |
| [BEVFusion](https://github.com/mit-han-lab/bevfusion) via [MMDetection3D](https://mmdetection3d.readthedocs.io/en/latest/model_zoo.html) | Base fused detector plus camera-only and LiDAR-only baselines, with nuScenes checkpoints | Apache-2.0 code |
| TransFusion-L or CenterPoint via [OpenPCDet](https://github.com/open-mmlab/OpenPCDet) | Second LiDAR branch to show the wrapper is model-agnostic | Apache-2.0 |
| [Depth Anything V2 Small](https://github.com/DepthAnything/Depth-Anything-V2) | Monocular depth for the depth-residual check | Apache-2.0 for the Small model only; larger sizes are CC-BY-NC |

**Software**

| Layer | Tools |
| --- | --- |
| Core | Python 3.10, PyTorch, MMDetection3D 1.4, nuscenes-devkit, NumPy, SciPy |
| Geometry | Open3D, Numba for ray casting in free-space and shadow checks |
| Attribution head | LightGBM or XGBoost, scikit-learn |
| Conformal and sequential tests | Written in-house (about 300 lines); MAPIE as a cross-check |
| Experiment control | Hydra configs, MLflow tracking, DVC or plain manifests for data versions, pytest |
| Closed loop | CARLA Python API, its built-in BehaviorAgent as the planner, ScenarioRunner for scripted scenarios |
| HPC | Slurm job arrays, Apptainer containers (Docker is normally not allowed on shared clusters) |
| Writing | LaTeX, Matplotlib |

No paid API, dataset or simulator is required at any stage.

**Added for Witness**

| Tool | Use | Licence |
| --- | --- | --- |
| [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) 2B to 8B | Narrator; 2B for laptop development, 8B on one A100 | Apache-2.0 per the model cards; confirm at stage 0 |
| Hugging Face Transformers | Runs the narrator locally, no API | Apache-2.0 |
| Open3D, Matplotlib, FFmpeg | Replay rendering to PNG and MP4 | Already in the stack, plus FFmpeg (LGPL/GPL builds) |
| Gradio | Live trust view | Apache-2.0; confirm at stage 0 |
| Python `hashlib` | SHA-256 hash chain | Standard library |

**Added for the data science track**

| Tool | Use | Licence |
| --- | --- | --- |
| scikit-learn | Group splits, calibration metrics, domain classifier for DS3 | BSD-3-Clause |
| SHAP | TreeSHAP explanations for M3 (DS1) | MIT |
| Optuna | Hyperparameter search with scene-grouped cross-validation | MIT |
| statsmodels, SciPy | Holm-Bonferroni correction, paired tests, effect sizes (DS2) | BSD-3-Clause |
| pandera | Schema validation of the evidence table (DS2) | MIT |
| DuckDB | SQL queries over the parquet evidence table | MIT |

Licences are as far as I know; confirm each at stage 0 with the rest of the stack.

## 9. Experiments, baselines, metrics and required results

The thesis stands on three experiments (E1, E2, E4) run on nuScenes; the other four strengthen it. Each maps to one research question.

| Exp. | Question | Setup | Metrics |
| --- | --- | --- | --- |
| E1 Attribution | RQ1 | Clean, benign and attacked versions of nuScenes validation frames; leave-one-type-out | Three-way accuracy and macro-F1; attack-versus-benign AUROC; false-quarantine rate against the chosen level; detection delay in frames |
| E2 Detection quality | RQ2 | Same data, detector output after response | mAP and NDS per condition; attack success rate; share of lost mAP recovered |
| E3 Calibration | RQ1, RQ2 | Held-out calibration and test scenes | Expected calibration error of existence probability; trust calibration error of the cause posterior; realized in-corridor miss rate against its bound |
| E4 Cost | RQ3 | Timed runs on one GPU type | Latency per frame by tier; share of objects escalated; accuracy-versus-budget Pareto curve |
| E5 Closed loop | RQ4 | CARLA scenarios crossed with clean, fog or rain, ghost ahead, hidden lead vehicle, patch | Collision rate; phantom hard-brake count; route completion; minimum time-to-collision |
| E6 Adaptive attacker | RQ5 | Attacks A5 to A7 | Attack success with and without the defense; attacker cost (points or patch area needed) |
| E7 Generality | All | Second base detector; KITTI subset | Change in E1 and E2 headline numbers |

**E8, Witness faithfulness and hijack resistance (added, tests H6).** Generate capsules for 200 flagged events spread across nominal, degraded and attack causes. Compare three narrators: template only, VLM without the verifier, and VLM with the verifier. Report grounded-claim rate, ungrounded claims released, cause-label flips under attack A8, semantic-note accuracy and time per report. An optional reader study asks 8 to 10 people to name the cause from a capsule versus raw logs; ask the advisor whether it needs IRB review. E8 adds figure 8: one capsule for a ghost-object attack beside one for fog.

**E9, data science analyses (added).** Runs on the outputs of stages 5, 6 and 8 and tests H7. (a) Explainability: global and per-class SHAP importance for M3, plus the metadata-only leakage classifier (DS1, DS2). (b) Shift: for each held-out condition, domain-classifier AUC and maximum mean discrepancy from the training evidence, with attribution accuracy and false-quarantine rate plotted against them (DS3). (c) Cost: expected-cost curves over cost ratios from 10:1 to 1000:1, restricted to operating points that keep the conformal bound (DS4). Adds figures 9 to 11.

**Baselines**

| ID | Baseline | Why it is needed |
| --- | --- | --- |
| B0 | BEVFusion unmodified | Reference for every number |
| B1 | LiDAR-only and camera-only branches | Shows what fusion adds and loses |
| B2 | Uncertainty-weighted late fusion in the style of UMoE | The "one scalar" approach this thesis argues against |
| B3 | Conflict-discount fusion in the style of ECoLaF | Conflict-aware but not cause-aware |
| B4 | Free-space and shadow checks alone, in the style of CARLO and Shadow-Catcher | Security defense without a benign control |
| B5 | Single-envelope anomaly detector | Detects "something is off" with no attribution |
| B6 | Dual-threshold conformal abstention | Strongest statistical baseline |

B2 to B4 are re-implementations on the same base detector where original code does not fit; the thesis should say so plainly.

**Ablations.** Remove each evidence family (U, P, S, counterfactual) in turn; single versus dual envelope; scheduler off (all tiers on every object); trust tracker off.

**Statistics.** Three seeds for every trained head, bootstrap confidence intervals over scenes, paired tests against B0 and B2.

**Added statistics (data science track, DS2).** Bootstrap by scene, not by frame, because frames within a scene are correlated. Holm-Bonferroni correction across all baseline comparisons. Effect sizes reported beside every p-value. ECE, Brier score and reliability diagrams for the attribution head. A metadata-only leakage classifier is reported next to every attribution result.

**Figures and tables the thesis must contain**

1. Scatter of uncertainty against physical-consistency score, coloured by true cause. This is the figure that proves or kills the core claim, so produce it first.
2. Leave-one-type-out attribution confusion matrix.
3. mAP and NDS table across all conditions and baselines.
4. Martingale traces over time for a fog onset and for an attack onset.
5. Latency-accuracy Pareto curve with the scheduler on and off.
6. CARLA closed-loop table.
7. Adaptive-attacker curve: attack success against attacker cost.
8. Witness capsule figure from E8 (planned in E8).
9. SHAP summary plot for the attribution head, by cause class (E9a).
10. Attribution accuracy and false-quarantine rate against shift distance, one point per held-out condition (E9b).
11. Expected cost against cost ratio, default threshold versus cost-aware threshold, with the false-alarm bound marked (E9c).

## 10. Patentability

Four parts of the design look claimable, but nobody can promise a patent from a literature search; a registered patent attorney or the university's commercialization office has to run a formal prior-art search. This section is technical input for that conversation, not legal advice.

**Candidate claims, strongest first**

| Candidate | Claim in plain words | Why it may be new | Closest prior art to distinguish |
| --- | --- | --- | --- |
| A. Dual-envelope cause attribution | Compute two sequential test statistics per sensor against a nominal reference and a nominal-plus-benign reference; classify the anomaly cause by which statistics cross their thresholds; select a fusion action by cause | No work found pairs two reference envelopes to split benign from adversarial in a vehicle fusion stack | [US 12,106,575](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12106575) (natural versus adversarial for camera images); [martingale shift-cause monitors](https://ar5iv.labs.arxiv.org/html/2407.21748) |
| B. Counterfactual modality masking | Mask one modality's features inside an object's region of a shared BEV map, re-run only the fusion head, and combine the existence change with a physical-consistency score to assign blame to a sensor | Existing checks compare detections or raw data; none found intervenes on fused features at runtime | LIFE and the cross-check defenses in the [frustum paper](https://www.usenix.org/system/files/sec22fall_hallyburton.pdf); [CARLO](https://arxiv.org/abs/2006.16974) |
| C. Risk-budgeted verification | Order verification tiers by cost and assign them to objects by suspicion times driving criticality under a per-frame time budget | Verification in prior work is uniform | [US 12,374,122](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12374122) (object verification that instructs the planner) |
| D. Trust-calibrated output contract | Emit each object with a cause posterior and a confirmed, cautious or rejected label that the planner maps to distinct behaviours | Weakest alone; useful as a dependent claim | [MATE](https://arxiv.org/abs/2503.04954) trust-weighted fusion |

**Candidate claim E (added): evidence-locked incident capsule.** A method that, for each perception anomaly, stores a cause label from a statistical attribution, a counterfactual re-detection with the suspect modality masked, and a generated report in which every claim is machine-verified against the stored evidence, all linked in a hash chain. Closest prior art to check: the VehicleSec 2025 language-model paper, DSSAD and event-recorder patents such as US 12,487,281 (found in search, not read), and explainable-driving patents. E depends on claims A and B, which strengthens the combination argument.

**What makes the claims stronger**

- Tie every claim to a concrete sensor-processing improvement with measured results (fewer false quarantines, recovered detection accuracy). Abstract "classify then act" wording is where software claims usually fail eligibility review.
- Claim the combination A plus B plus cause-specific response as the main independent claim, with C and D as dependents.
- Keep dated lab notes and commit history; they document conception and reduction to practice.

**Order of operations**

1. Keep the code repository private from day one.
2. File an invention disclosure with the Texas A&M commercialization office once E1 shows the core claim holds. Research done with university resources is normally university-owned, so confirm the policy and inventor share with them and with the advisor.
3. Only after a provisional application is filed: post to arXiv, open the repository, defend publicly. A public defense, preprint or public repository counts as disclosure. The United States allows a one-year grace period after one's own disclosure; most other countries allow none.

**Honest risk.** The individual pieces (uncertainty, consistency checks, conformal tests, trust filters) are all published. Novelty rests on the specific combination and on cause attribution. If an examiner finds a 2026 paper that already does dual-envelope attribution for vehicle sensors, claim A narrows to its details, and B becomes the lead claim.

## 11. Build stages for Claude Code or Codex

The build is twelve stages, each ending in a check that can pass or fail. Give the coding agent one stage at a time, with this document and the repository as context. Stage 3 is a go/no-go gate for the whole thesis.

**Rules to put in the repository's `CLAUDE.md` / `AGENTS.md` before stage 0**

- Never invent a number. Every figure in a table comes from a logged run with a config hash and commit ID.
- Base detectors stay frozen. Only code under `discern/` and small heads are trained.
- Held-out attack and corruption types are listed in `splits/heldout.yaml`. A test fails the build if any appears in a training or calibration manifest.
- Cache heavy outputs (detections, BEV features, evidence tables) to disk; later stages read caches, never re-run backbones.
- Tests first for geometry and statistics code. One pull request per stage, with a short `RESULTS.md` entry.
- Attack code is for simulation on recorded data and CARLA only.

**Repository layout**

```
discern-av/
  CLAUDE.md  AGENTS.md  README.md  RESULTS.md
  configs/            # Hydra: data, model, perturb, monitor, experiment
  splits/             # scene lists, heldout.yaml
  discern/
    data/             # nuScenes access, caching, manifests
    base/             # wrappers for BEVFusion and single-modality branches
    perturb/          # benign/ and attacks/ behind one interface
    evidence/         # uncertainty.py physical.py scene.py counterfactual.py
    monitor/          # conformal p-values, martingales, envelopes
    attribute/        # head, calibration
    respond/          # reweight, quarantine, trust tracker, output contract
    schedule/         # criticality, tier allocation
    eval/             # metrics, bootstrap, figure scripts
    carla_loop/       # sensor rig, agent adapter, scenarios, injectors
  baselines/          # B2 to B6
  hpc/                # Slurm templates, Apptainer definition
  tests/
```

### Stage 0. Environment and scaffold

- **Goal:** a reproducible environment on a laptop and on HPRC.
- **Build:** repository skeleton above; conda environment file; Apptainer definition with PyTorch, MMDetection3D and BEVFusion ops compiled; Hydra config tree; MLflow local tracking; pytest and a lint check.
- **Human steps:** register at nuscenes.org and download the mini split; request or confirm an HPRC allocation with GPU access.
- **Done when:** `pytest` passes and BEVFusion inference runs end to end on nuScenes mini inside the container.
- **Runs on:** laptop for scaffold; one HPRC GPU for the container test.

### Stage 1. Data layer and base detectors

- **Goal:** trusted baselines and caches.
- **Build:** manifest builder for nuScenes validation and a 100-scene slice of train (half for fitting heads, half for calibration); wrappers that run the fused model and the LiDAR-only and camera-only branches; hooks that save detections, heatmaps and the camera and LiDAR BEV feature maps before fusion.
- **Done when:** the fused model lands within about 0.5 points of the published validation scores (68.5 mAP, 71.4 NDS in the [BEVFusion repository](https://github.com/mit-han-lab/bevfusion)) and caches exist for every frame.
- **Runs on:** HPRC, full nuScenes on scratch storage.
- **Data science add-on:** a data profile of the cache (object counts by class, distance band and scene type; frames with a missing sensor) saved as `reports/data_profile.html`; the scene-grouped split manifest is frozen and hashed here so no later stage can leak frames across splits.

### Stage 2. Perturbation engine

- **Goal:** paired clean, benign and attacked versions of the same frames, with ground-truth cause labels.
- **Build:** one `Perturbation` interface returning modified sensor data plus metadata (cause, sensor, affected region, severity, seed). Benign side: MultiCorrupt generators and selected nuScenes-C types. Attack side: A1 to A4 re-implemented at data level from the cited papers, with physical limits as config values (point budget, patch size, placement range). Visual dump tool for spot checks.
- **Done when:** every perturbation is deterministic under a seed, unit-tested, and the unmodified detector's mAP, NDS and attack success rate are tabulated per perturbation.
- **Runs on:** HPRC job array, one job per perturbation type.
- **Data science add-on:** a label table with cause, sensor, severity and seed per perturbed frame, validated by a pandera schema; class balance per cause reported; the sampling plan for E1 fixed here (stratified by cause and severity) before any model is trained.

### Stage 3. Evidence extractors and the go/no-go figure

- **Goal:** test the core claim before building anything else.
- **Build:** uncertainty features from head-only dropout passes; physical checks (free space, shadow, density law, depth residual with Depth Anything V2 Small, radar agreement, track kinematics, local image energy); scene-context features; one parquet table with a row per object per condition.
- **Done when:** figure 1 exists and a plain logistic regression on these features separates attack from benign on held-out types.
- **Gate:** AUROC under roughly 0.75 means the features are not enough. Stop, inspect failure cases, add or fix features. Do not proceed on hope.
- **Runs on:** HPRC for extraction; laptop for analysis.
- **Data science add-on:** pandera schema on the evidence parquet; a feature correlation matrix with near-duplicate features flagged; the metadata-only leakage classifier (DS2) run beside the logistic regression, and the gate also requires it to stay well below the evidence model; a DuckDB notebook for exploring the table.

### Stage 4. Dual-envelope monitors

- **Goal:** sequential tests with a false-alarm bound that holds in practice.
- **Build:** nonconformity score per sensor stream; conformal p-values against a fixed reference set; betting martingale with a mixture of bet sizes; two envelopes (clean, clean-plus-benign); stream simulator that stitches scene sequences with a condition onset at a known frame.
- **Done when:** over at least 1,000 simulated clean and in-envelope benign streams the empirical rate of ever flagging an attack is at or below the chosen level, and median detection delay for A1 to A4 is reported. Follow the fixed-reference construction in [conditional conformal test martingales](https://arxiv.org/abs/2602.13848) to avoid contamination of the reference set.
- **Runs on:** laptop or a CPU node.
- **Data science add-on:** a histogram of conformal p-values on clean streams, which should be close to uniform; a strong departure means the reference set or the score is wrong.

### Stage 5. Attribution head and calibration

- **Goal:** experiment E1 and E3.
- **Build:** gradient-boosted head on evidence plus monitor states; temperature scaling; leave-one-type-out training harness; metrics and confusion matrices with bootstrap intervals.
- **Done when:** E1 and E3 tables are generated by a single command from caches, across three seeds.
- **Runs on:** laptop or CPU node.
- **Data science add-on:** class weighting for imbalance; Optuna search with scene-grouped cross-validation; ECE, Brier score and reliability diagrams; TreeSHAP global and per-class plots, with per-event SHAP values written to the evidence record for Witness (DS1); domain-classifier and MMD shift distances per held-out condition (DS3). Outputs feed E9a and E9b.

### Stage 6. Response, counterfactual ablation and trust tracker

- **Goal:** experiment E2.
- **Build:** variance inflation and re-weighting for degraded; BEV feature masking inside an object region with a re-run of fusion layers and head only; blame assignment rule; Beta-Bernoulli trust filter per track and sensor region; output contract with confirmed, cautious and rejected labels; conformal risk control for the in-corridor miss bound.
- **Done when:** the mAP and NDS table across all conditions is generated, clean-data loss is measured, and masking is verified by a test that hides a real object when both modalities are masked.
- **Runs on:** HPRC GPU.
- **Data science add-on:** cost matrix as config values; expected-cost curves over the cost-ratio range; the chosen threshold is constrained to keep the conformal bound (DS4). Output feeds E9c.

### Stage 6b. Witness: incident capsules and live trust view

- **Goal:** every flagged event yields a verifiable capsule, and one command renders a demo video. Start only after the stage 3 gate has passed.
- **Build:** a new package `discern/witness/`.
  - `record.py`: the evidence record as a frozen dataclass with a JSON schema, filled from M1 to M6 outputs.
  - `replay.py`: three-panel render (camera mosaic with boxes, LiDAR bird's-eye view, re-detection with the suspect modality masked) to PNG and MP4.
  - `narrate.py`: Qwen3-VL through Transformers; the prompt treats all scene text as data; output is constrained JSON with `claims[{text, evidence_keys}]` and `semantic_note`.
  - `verify.py`: deterministic checks that each cited key exists, quoted numbers match within tolerance, and the cause equals the M3 label; on failure, emit the template report.
  - `chain.py`: SHA-256 hash chain and a `verify_chain` command.
  - `dashboard.py`: Gradio app for the live trust view.
  - `discern/perturb/scene_text.py`: renders injected text into camera images for attack A8.
- **Tests:** the verifier rejects 20 hand-written bad reports; the chain check fails when one byte of a stored capsule is flipped.
- **Done when:** capsules exist for 200 events across all causes; the H6 table from experiment E8 is in `RESULTS.md`; a 60 to 90 second video shows a ghost-object attack and a fog event side by side.
- **Runs on:** laptop with the 2B narrator for development; one A100 on HPRC for the 8B narrator and the E8 run. Narrator time is reported separately and is not part of the H4 latency budget.

### Stage 7. Risk scheduler and timing

- **Goal:** experiment E4.
- **Build:** ego-corridor and time-to-collision criticality from nuScenes ego pose and tracks; tier allocation under a millisecond budget; per-tier timers.
- **Done when:** the Pareto curve exists and scheduler-on stays within the latency target while keeping at least 95% of scheduler-off attribution accuracy on in-corridor objects.
- **Runs on:** one fixed GPU type for all timing runs; record the model.

### Stage 8. Baselines and ablations

- **Goal:** fair comparisons.
- **Build:** B2 to B6 on the same caches and base detector; ablation switches as config flags.
- **Done when:** one command regenerates the full comparison and ablation tables.
- **Runs on:** HPRC job array.
- **Data science add-on:** scene-clustered bootstrap, Holm-Bonferroni correction and effect sizes applied to every comparison and ablation (DS2); the E9 tables and figures 9 to 11 regenerate from the same command.

### Stage 9. Adaptive attacks

- **Goal:** experiment E6.
- **Build:** A5 frustum placement, A6 coordinated phantom, A7 with the monitor score in the attack objective.
- **Done when:** the attack-success-versus-attacker-cost curve is produced, and the write-up states which attacks still succeed.
- **Runs on:** HPRC GPU; patch optimization is the most expensive job in the project.

### Stage 10. CARLA closed loop

- **Goal:** experiment E5.
- **Build:** sensor rig matching nuScenes geometry as closely as CARLA allows; adapter feeding DISCERN-AV output to CARLA's BehaviorAgent in place of ground truth; injectors that apply A1 to A4 and weather to live sensor streams; 5 scenario families with 10 seeds each.
- **Known issue:** the detector was trained on real data, so accuracy drops in simulation. Fine-tune only the detector heads on CARLA-generated frames, or report results relative to the same detector without the wrapper. Say which in the thesis.
- **Done when:** the closed-loop table is generated from logged runs with video for one example per scenario.
- **Runs on:** a GPU with offscreen rendering. Try HPRC with the CARLA container first; fall back to a lab workstation.

### Stage 11. Generality (optional)

- **Goal:** experiment E7.
- **Build:** swap in a second base detector through the same wrapper interface; run E1 and E2 on a KITTI subset.
- **Done when:** headline numbers are reported for both.

### Stage 12. Reproducibility and writing

- **Goal:** a thesis and a paper that anyone can regenerate.
- **Build:** `make all-figures` from caches; environment lock files; model card and data statement with licences; thesis chapters mapped to experiments; a short paper draft.
- **Done when:** a clean clone plus caches reproduces every table, and the repository is still private pending the disclosure decision in section 10.
- **Data science add-on:** package DISCERN-Evidence with its datasheet, data card and baseline notebook (DS5); keep it private until the disclosure decision and the nuScenes licence check.

### Stage 13. Committee demo console (frontend)

- **Goal:** one browser app that lets a committee member see what DISCERN-AV does in five minutes, without reading code or tables.
- **Design decision:** the console replays results that were already computed. It reads the cached detections, trust labels and Witness capsules from earlier stages, so it runs on a laptop with no GPU and no internet. A defense demo that depends on a live cluster job is a demo that can fail in the room.
- **Build:** a `demo/` folder with a FastAPI backend (`demo/api/`) that serves scenes, per-frame records and capsules from a `demo_pack/` directory, and a React + Vite + TypeScript frontend (`demo/web/`) with three.js for the LiDAR view. A `make demo-pack` command exports 6 to 8 curated scenes (clean, fog, rain, camera patch, LiDAR spoof, coordinated phantom, one failure case). A `make demo` command starts everything on localhost.
- **Screen 1, Drive view:** pick a scene and a condition. Synced camera images and a bird's-eye LiDAR view play together, with every object boxed in its trust colour (confirmed, cautious, rejected) and a timeline that marks each flagged event.
- **Screen 2, With and without:** the same scene side by side, base detector alone on the left and DISCERN-AV on the right. This is the screen that shows the ghost car being accepted on one side and rejected on the other.
- **Screen 3, Incident capsule:** click a flagged event to open its capsule: the muted-sensor replay, the evidence overlay, and the report. Each sentence in the report links to the evidence field it cites and shows its verified mark. The semantic note is shown separately and labelled unverified.
- **Screen 4, Tamper check:** a button runs `verify_chain` on the log. A second button edits one byte in a copy of the log and runs it again, so the audience sees the chain break.
- **Screen 5, Results:** the thesis tables and figures loaded from `RESULTS.md` outputs, with H1 to H6 each marked met or not met from the logged numbers. Nothing on this screen is typed by hand.
- **Screen 6, Closed loop (only if stage 10 is done):** recorded CARLA runs with the trust view beside the driving video, wrapper on and wrapper off.
- **Relation to stage 6b:** the Gradio dashboard stays as the developer tool. The console reads the same capsule files, so no experiment is re-run for it.
- **Tests:** a Playwright smoke test opens each screen and plays one scene; an API test checks that every capsule in the demo pack passes `verify_chain`.
- **Done when:** `make demo` works on a clean laptop with the network off, a written five-minute walkthrough script exists in `demo/WALKTHROUGH.md`, and a screen recording of that walkthrough is saved as a backup for the defense.
- **Licence note:** the demo pack contains nuScenes images, which are under non-commercial terms. Run the console locally or on a university machine and do not host it on the public web without checking the nuScenes terms. FastAPI, React, Vite and three.js are MIT-licensed as far as I know; confirm at stage 0.
- **Runs on:** laptop. About one week, by my estimate. It can be built any time after stage 6b, so it does not have to wait for CARLA.
- **Data science add-on:** an "Under the hood" panel on screen 3 showing the SHAP explanation for the event being viewed, and on screen 5 the reliability diagram, the shift-distance plot and the expected-cost curve, with H7 marked met or not met alongside H1 to H6.

## 12. Compute plan, schedule, risks and fallbacks

A laptop is enough for stages 0, 4 and 5; everything touching full nuScenes or patch optimization belongs on HPRC. No stage trains a large model, so the heaviest work is inference sweeps and attack optimization.

**Compute**

| Work | Where | Notes |
| --- | --- | --- |
| Scaffold, statistics, attribution head, analysis | Laptop or CPU node | Reads cached parquet tables |
| Base inference and caching, perturbation sweeps, evidence extraction | [HPRC](https://hprc.tamu.edu/resources/) Grace or FASTER, A100 GPUs | Slurm job arrays; one condition per job |
| Patch optimization (A3, A7), counterfactual sweeps | Grace A100, or ACES H100 if allocated | Largest GPU-hour item |
| CARLA closed loop | HPRC GPU with offscreen rendering, else a lab workstation | Decide at stage 10 |
| Storage | HPRC scratch | Full nuScenes is several hundred GB; cached BEV features add more. Store features as float16 and only for the frames used |

**Schedule in working weeks (with a coding agent doing most implementation)**

| Weeks | Stages | Output |
| --- | --- | --- |
| 1 | 0, 1 | Environment, reproduced baselines, caches |
| 2 | 2 | Perturbation engine, degradation table |
| 3 | 3 | Evidence table, go/no-go figure |
| 4 | 4, 5 | Monitors, attribution results E1 and E3 |
| 5-6 | 6, 7 | Response, scheduler, E2 and E4 |
| 7 | 8 | Baselines and ablations |
| 8 | 9 | Adaptive attacks, E6 |
| 9-10 | 10 | CARLA closed loop, E5 |
| 11-12 | 11, 12 | Generality, writing, disclosure |
| 13 | 13 | Committee demo console, walkthrough script, backup recording |

**Minimum viable thesis.** Stages 0 to 6 plus B0, B2 and B4, on nuScenes only, with attacks A1 to A4. That is about six weeks and already answers RQ1 and RQ2 with held-out generalization. CARLA and the adaptive attacker then become extensions.

**Effect of Witness on the plan.** Stage 6b adds about one week, by my estimate, so the minimum thesis becomes stages 0 to 6b in about seven weeks. It needs no CARLA and no training. The main risk is narrator hallucination, which the verifier and the template fallback contain; if Qwen3-VL proves unreliable, the template-only capsule still delivers the replay, the overlay and the hash chain.

**Effect of the data science track on the plan.** DS1 to DS5 add about four to five working days by my estimate, spread across existing stages rather than a new stage, and all of it runs on a laptop or CPU node. The minimum viable thesis should include DS1, DS2 and DS3, because they strengthen the core attribution claim; DS4 and DS5 can follow.

**Risks**

| Risk | What happens | Fallback |
| --- | --- | --- |
| Core claim fails at the stage 3 gate | Attack and benign overlap in evidence space | Narrow scope to the pairs that do separate (for example LiDAR spoofing against fog and snow), and publish the attribution benchmark with the negative finding |
| BEVFusion build problems | Custom CUDA ops and pinned old versions fail to compile on the cluster | Use the OpenPCDet BEVFusion implementation, or a prebuilt MMDetection3D container; pin versions in the Apptainer file |
| Synthetic corruptions look unlike real weather | Reviewers question false-quarantine numbers | Report the real nuScenes rain and night scenes as a separate row |
| Guarantee is narrower than it sounds | The bound covers benign conditions inside the reference envelope only; a new benign condition can be flagged as suspected attack | Name the third class "outside benign envelope" in the thesis, report its rate on held-out corruptions, and treat it conservatively in the response |
| Simulation gap in CARLA | Real-trained detector is weak on rendered data | Head-only fine-tune on CARLA frames, or report relative change only |
| CARLA will not render on HPRC | Closed-loop runs blocked | Lab workstation; if none, replace E5 with open-loop planning-relevance metrics on nuScenes and state the limitation |
| Adaptive attacker defeats the defense | H5 fails | Report it as the mapped limit; show attacker cost increase |
| Scooped during the project | A similar paper appears | The benchmark and the dual-envelope guarantee are separable contributions; re-run the prior-art search before submission |

## 13. Sources

Pages retrieved during this survey, 15 November 2026. Benchmark repositories on GitHub could not be opened from this session, so their details come from the linked papers; check each repository's licence file at stage 0.

**Uncertainty, conflict and conformal fusion**

- [Uncertainty-Encoded Multi-Modal Fusion (UMoE)](https://arxiv.org/abs/2307.16121)
- [Uncertainty-Aware Evidential Fusion, preprint](https://www.preprints.org/manuscript/202601.0488)
- [Conflict-Guided Evidential Multimodal Fusion (ECoLaF)](https://mlanthology.org/wacv/2025/deregnaucourt2025wacv-conflictguided)
- [Eliminating Cross-modal Conflicts in BEV Space (ECFusion)](https://arxiv.org/abs/2403.07372)
- [MI-calibrated Conformal Feature Fusion](https://arxiv.org/abs/2309.09593)
- [Dual-Threshold Conformal Prediction with Abstention](https://arxiv.org/abs/2502.07255)
- [Pitfalls and Promise of Conformal Inference Under Adversarial Attacks](https://arxiv.org/abs/2405.08886)
- [Conditional Conformal Test Martingales](https://arxiv.org/abs/2602.13848)
- [Martingale runtime monitors for shift cause](https://ar5iv.labs.arxiv.org/html/2407.21748)

**Attacks, defenses and systematizations**

- [Fusion Is Not Enough](https://arxiv.org/abs/2304.14614)
- [Adversarial Robustness of LiDAR-Camera Fusion](https://arxiv.org/abs/2312.01468)
- [Security Analysis of Camera-LiDAR Fusion (frustum attack)](https://www.usenix.org/system/files/sec22fall_hallyburton.pdf)
- [Cross-Modal Phantom](https://arxiv.org/abs/2604.21841)
- [CARLO](https://arxiv.org/abs/2006.16974)
- [Shadow-Catcher](https://arxiv.org/abs/2008.12008)
- [ADoPT](https://arxiv.org/abs/2310.14504)
- [MATE: Multi-Agent Trust Estimator](https://arxiv.org/abs/2503.04954)
- [AD2](https://arxiv.org/abs/2602.10160)
- [Selective sensor substitution for depth resilience](https://arxiv.org/abs/2604.12418)
- [SoK: Perception Attacks and Multi-Sensor Fusion](https://arxiv.org/abs/2604.20621)
- [SoK: How Sensor Attacks Disrupt Autonomous Vehicles](https://arxiv.org/abs/2509.11120)

**Benchmarks, data, tools**

- [MultiCorrupt](https://arxiv.org/abs/2402.11677)
- [Robo3D](https://ldkong.com/Robo3D)
- [Benchmarking Robustness of 3D Object Detection to Common Corruptions](https://arxiv.org/abs/2303.11040)
- [MSC-Bench](https://arxiv.org/abs/2501.01037)
- [PSA-Fusion: Unity is Strength?](https://doi.org/10.1145/3589334.3645612)
- [Safety2Drive](https://arxiv.org/abs/2505.13872)
- [Bench2Drive](https://arxiv.org/abs/2406.03877)
- [nuScenes Revisited](https://arxiv.org/abs/2512.02448)
- [CARLA downloads, 0.9.16](https://carla.readthedocs.io/en/0.9.16/download/) and [CARLA repository](https://github.com/carla-simulator/carla)
- [BEVFusion](https://github.com/mit-han-lab/bevfusion), [MMDetection3D model zoo](https://mmdetection3d.readthedocs.io/en/latest/model_zoo.html), [OpenPCDet](https://github.com/open-mmlab/OpenPCDet)
- [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2)
- [Texas A&M HPRC resources](https://hprc.tamu.edu/resources/)

**Patents**

- [US 12,106,575: natural versus adversarial perturbation verification](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12106575)
- [US 12,374,122: object detection verification for vehicle perception](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12374122)

**Added 15 Nov 2026: real-world problems and explanation work (for Witness)**

- [Electrek on NHTSA EA26002, Tesla FSD reduced-visibility probe](https://electrek.co/2026/03/19/nhtsa-upgrades-tesla-fsd-visibility-investigation-3-2-million-vehicles/) (opened)
- [Drive Tesla Canada on the closure of phantom-braking probe PE22002](https://driveteslacanada.ca/news/tesla-phantom-braking-investigation-closed-nhtsa/) (opened)
- [TRL summary on ADS approval and DSSAD](https://www.trl.co.uk/Uploads/TRL/Brochures/Regulatory%20preparation%20for%20ADS%20approval_Summary.pdf) (opened)
- [The Register on CHAI, prompt injection by road sign](https://www.theregister.com/2026/01/30/road_sign_hijack_ai/) (opened)
- [Lost in Fog: sensor perturbations and driving VLA reasoning, arXiv 2605.21446](https://arxiv.org/abs/2605.21446) (abstract opened)
- [From Detection to Explanation: LLMs for adversarial scenario analysis, VehicleSec 2025](https://www.usenix.org/conference/vehiclesec25/presentation/fernandez) (opened)
- [PhysNav-DG, arXiv 2505.01881](https://arxiv.org/abs/2505.01881) (search summary only)
- [Qwen3-VL repository](https://github.com/QwenLM/Qwen3-VL) (search summary only; GitHub could not be opened from here)

**Added 17 Nov 2026: data science methods**

- [Lundberg and Lee, A Unified Approach to Interpreting Model Predictions (SHAP), arXiv 1705.07874](https://arxiv.org/abs/1705.07874)
- [Gebru et al., Datasheets for Datasets, arXiv 1803.09010](https://arxiv.org/abs/1803.09010)
