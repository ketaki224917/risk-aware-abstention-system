# Decisions

## ADR-001: Treat workspace as a fresh implementation [DECISION] Date: 2026-10-25 Status: active
Context: Initial inventory found no project files, paper, data archive, results, or Git history.
Options considered: Guess at an existing code path; or record that the original implementation cannot be inspected and create a new implementation from the supplied specification.
Decision and why: Treat this as a fresh implementation. Do not claim that any existing path produces paper results, and do not claim reproduction until an actual run produces evidence.
Consequences / how to reverse: Results from this implementation must be clearly separated from paper target values. If the original source or paper is later supplied, inventory it and supersede this ADR with evidence.

## ADR-002: Preserve the prompt as repository instructions [DECISION] Date: 2026-10-25 Status: active
Context: User's prompt explicitly requests that it be saved at the repository root as `AGENTS.md`.
Options considered: Summarize it; or copy the attachment without changing its content.
Decision and why: Copy the attachment verbatim so subsequent sessions retain the full project specification.
Consequences / how to reverse: Edit only through a follow-up instruction or a superseding decision.

## ADR-003: Record unspecified risk-component values as explicit assumptions [ASSUMPTION] Date: 2026-10-25 Status: superseded by ADR-009
Context: The supplied prompt specifies that benign predictions carry a higher consequence but does not provide numeric consequence values or bootstrap member size. The source paper/code was absent.
Options considered: Invent hidden values; tune values to paper targets; or choose transparent bounded values and label the choice.
Decision and why: Use C(predicted malignant)=0 and C(predicted benign)=1, and 50 trees per bootstrap member. These are simple bounded assumptions that preserve the specified ordering. They are not clinically derived. Use the prompt's fixed 0.5/0.2/0.3 risk weights.
Consequences / how to reverse: All values are in config.yaml and consequence variations are logged in sensitivity.csv. Replace only with source-backed values and a superseding ADR; never tune to force target metrics.

## ADR-004: Fit component ranges on validation and clip test transforms [DECISION] Date: 2026-10-25 Status: superseded by ADR-009
Context: U, A, and C must be normalized without test leakage; U and A have score ranges dependent on each fitted model.
Options considered: Train-fitted ranges; validation-fitted ranges; or pooled train/validation ranges.
Decision and why: Fit min/max for U and A on validation predictions only, clip later transforms to [0,1], and use the bounded consequence value directly. Select thresholds from validation risk with NumPy linear percentile interpolation.
Consequences / how to reverse: Test values outside validation extrema saturate at 0/1. This follows the prompt's validation-only threshold/normalization rule. A different method needs an ADR and a logged sensitivity comparison.

## ADR-005: Keep the fixed policy after target discrepancies [DECISION] Date: 2026-10-25 Status: superseded by ADR-009
Context: Run raa-20261025-01 found full-policy accepted error 1.493% versus a ≈0.70% target; uncertainty-only selective accuracy exceeded full by 0.783 percentage points. The pooled synthetic-shift AUROC over all 12 variants was 0.731, while the 10-feature/2σ variant was 0.921.
Options considered: Change the fixed weights or threshold percentiles to match paper targets; report the logged values and sensitivity grid; or claim the paper target is reproduced from one selected stress variant.
Decision and why: Keep the prescribed 0.5/0.2/0.3 weights and 70/90 thresholds. Report all sensitivity and shift variants. Do not claim the full-policy error target is supported. Do not equate the pooled stress result to an unspecified paper recipe.
Consequences / how to reverse: The paper wording requires an author decision. See BLOCKERS.md. No parameter was tuned to a target.

## ADR-006: Define review workload as unweighted review cases [ASSUMPTION] Date: 2026-10-25 Status: active
Context: The prompt requests workload but provides no staff-time or cost model for Assisted versus Human Review.
Options considered: Invent weighted minutes/costs; or report separate level counts and an unweighted total.
Decision and why: Report Assisted and Human Review separately and define review workload as their sum in case counts/fraction. This is not a staff-time estimate.
Consequences / how to reverse: A real workflow cost model would require evidence and a superseding ADR.

## ADR-007: Bootstrap confidence intervals for stress variants by held-out case [DECISION] Date: 2026-10-25 Status: active
Context: Synthetic variants reuse the same held-out test cases. Independent resampling would treat repeated perturbations of one case as independent observations.
Options considered: Resample clean and shifted scores independently; or resample case IDs and retain all variants for each sampled ID.
Decision and why: Use a paired case bootstrap for each variant and for the pooled 12-variant AUROC. All perturbations belonging to a sampled test case stay together in each replicate.
Consequences / how to reverse: The paired interval is stored in stress_test.json/CSV. The test cases are still one split, and the interval does not quantify between-split variation; the exact paper recipe is unknown.

## ADR-008: Fix and record all experiment seeds [DECISION] Date: 2026-10-25 Status: superseded by ADR-009
Context: Reproducibility requires deterministic split, model, stress, and bootstrap randomness.
Options considered: Use fresh random seeds; or store a fixed contiguous split-seed range plus explicit component offsets and separate analysis seeds.
Decision and why: Use split seeds 2026–2055; validation split seed is the outer seed + 1; classifier, bootstrap members, and Isolation Forest use configured offsets; synthetic stress uses 4242; confidence intervals use 20261025.
Consequences / how to reverse: All seeds live in config.yaml or are derived as documented in code. Changing them requires a new run ID and should not overwrite a prior result.

## ADR-009: Align implementation with the supplied journal paper [DECISION] Date: 2026-10-26 Status: active
Context: The author supplied the journal paper after the initial implementation. Sections 3-5 specify consequence values, uncertainty/anomaly scaling, the split seed ranges, the stress recipe, and the main-split checker evaluation.
Decision and why: Use consequence 0.4 for a predicted malignant class and 1.0 for a predicted benign class; scale uncertainty by validation p95; standardize Isolation Forest features on training data and scale -score_samples using training min/p99; use split seeds 0-29 and main seed 42; apply signed 3σ shifts to 8 randomly selected features per held-out case; evaluate the six stated fault categories on the main split. Use the same outer seed for both split operations and direct split-seed estimator states because these choices reproduce the paper's main-split classifier counts. The paper leaves exact random generator details unspecified, so those remaining choices are recorded as implementation assumptions.
Supersedes: ADR-003's consequence-value assumption, ADR-004's min/max validation scaling rule, ADR-005's initial target reconciliation, and ADR-008's seed offsets/range. The 50-tree member size from ADR-003 is confirmed by the paper. ADR-007's uncertainty about the stress recipe is resolved; its case-cluster bootstrap remains an analysis choice not specified by the paper.
Consequences / how to reverse: Use a new run ID for these source-aligned outputs. Do not claim source-code identity: the original repository and raw experiment archive remain unavailable.

## ADR-010: Keep app inference as a thin adapter over fitted pipeline [DECISION] Date: 2026-10-27 Status: active
Context: The replacement demo accepts complete and partial user-entered WDBC records, while policy and explanation behavior already live in the research pipeline.
Options considered: Duplicate prediction logic in the Streamlit app; put validation/imputation/UI concerns into `DecisionSystem`; or expose a small `raa.inference.predict_case` adapter that receives a fitted inference context and calls the existing pipeline.
Decision and why: Use `predict_case(features, measured_mask, context=...)` in `src/raa/inference.py`. It validates measured values, completes only masked fields through an optional pre-fitted transformer, then calls `DecisionSystem.predict`. The Streamlit app does not own classifier, uncertainty, anomaly, risk, routing, or explanation logic.
Consequences / how to reverse: The returned immutable `DecisionRecord` carries measured/estimated counts and input warnings as presentation metadata. The inference context must be built from train-only preprocessing and a pre-fitted system; no fitting happens during a case prediction. Supersede this ADR if a different public API is needed, with equivalence tests against `DecisionSystem.predict`.

## ADR-011: Select guided fields from train-only model importance [DECISION] Date: 2026-10-27 Status: active
Context: A normal user should enter only six measured WDBC values, and the prompt requires a data-driven field choice.
Options considered: Choose six fields by intuition; use importance across all 30 measurements; or rank only the ten `mean ...` measurements by the seed-42 Random Forest fitted on TRAIN rows.
Decision and why: Use the six highest `feature_importances_` among mean features, with stable original-column order for ties. A full configured seed-42 fit on the 60% TRAIN partition ranked mean concave points (0.09412098), mean concavity (0.05688183), mean radius (0.05089682), mean perimeter (0.04022380), mean area (0.03628787), and mean compactness (0.01413636) highest. No validation or test features/labels select fields. The UI may display the selected set in a more readable order.
Consequences / how to reverse: `select_guided_features` applies this rule and tests exclude non-mean fields. The actual importance table will be saved under `results/demo/` with the demo artifact. If a different training split or selection rule is adopted, regenerate that table and supersede this ADR.

## ADR-012: Estimate missing WDBC values with a TRAIN-only KNN imputer [DECISION] Date: 2026-10-27 Status: active
Context: Guided entry supplies six measured WDBC fields, while the real classifier, uncertainty, anomaly, consequence, risk, policy, and explanation pipeline expects all 30 fields.
Options considered: Fill missing fields with global constants or medians; refit an imputer during app use; or use distance-weighted KNN imputation fitted on the fixed TRAIN partition and reuse that saved transformer.
Decision and why: Use `KNNImputer(n_neighbors=5, weights='distance')`, fitted only on the seed-42 TRAIN features. The same pre-fitted transformer completes partial profiles before invoking `DecisionSystem.predict`. App loading and per-case prediction never call `fit`.
Consequences / how to reverse: Every partial result states how many fields were estimated and warns that bootstrap disagreement on the completed row is not calibrated to imputation uncertainty. This does not establish clinical validity. Replace only with a train-only alternative and comparative validation evidence.

## ADR-013: Treat range and geometry checks as warnings [DECISION] Date: 2026-10-27 Status: active
Context: User-entered WDBC-style measurements can be mistyped or differ from the training sample, while the data's mean radius/perimeter/area are shape summaries rather than exact circle measurements.
Options considered: Reject every out-of-training-range value or approximate geometry mismatch; silently accept it; or reject malformed/nonfinite/negative measured values and show non-blocking warnings for unusual ranges and large circle-approximation differences.
Decision and why: Reject nonnumeric, NaN/infinite, negative, and wrong-sized inputs. Warn when measured values fall outside per-feature TRAIN min/max. When mean radius and mean perimeter/area are all available, warn if their approximate circle relation differs by more than 50%; this is a verification hint, not a validity test. No warning changes the model output or routing.
Consequences / how to reverse: The UI can proceed after a user reviews a warning; the anomaly and risk pipeline sees the entered value as-is. If tolerance changes, update validation tests and explain the approximation.

## ADR-014: Save the demo bundle and select examples from held-out test rows [DECISION] Date: 2026-10-27 Status: active
Context: Streamlit reruns its script on interaction, so fitting the RF ensemble or imputers in the app would retrain on page loads. Example cards must come from the seed-42 held-out TEST partition with verifiable claims.
Options considered: Fit and cache models from within the app process; embed untracked local artifacts; or create a reproducible offline artifact under `results/demo/` and load it without any fit fallback.
Decision and why: `make demo-artifact` runs `python -m raa.app.prepare_demo_artifact` once, fitting the classifier/ensemble/anomaly detector on TRAIN, policy thresholds on validation, and imputer/bounds on TRAIN. The committed compressed bundle is `results/demo/model_bundle.joblib`; manifest, feature importance, and case catalog are alongside it. `load_demo_artifact` only loads/validates this bundle and has no training path. The app computes case predictions from the held-out seed-42 test features; card selectors use no other partition.
Consequences / how to reverse: The artifact is pinned to the locked scikit-learn environment and must be rebuilt if model/config/source changes. No entered app values are written to disk. Missing artifacts surface a command to prepare them; app page load never fits.
 
## ADR-015: Keep CSV triage strict, bounded, and in memory [DECISION] Date: 2026-10-27 Status: active
Context: Batch demo input must accept WDBC measurements while avoiding accidental collection of identifiers or unbounded uploads.
Options considered: Accept arbitrary extra columns and persist uploaded files; accept only the 30 named numeric WDBC fields in memory; or accept wider schemas and attempt to identify sensitive columns.
Decision and why: Accept exactly the 30 feature names in any column order, reject missing/duplicate/unexpected columns, validate each row with the same input API, and cap a batch at 100 rows. Template/upload/paste/result downloads use memory-backed Streamlit widgets and generated CSV strings; code never writes supplied rows to disk.
Consequences / how to reverse: Downloaded output contains row number, model lean, route, risk, referral reason and warnings, but does not echo feature values. Row-limit changes require updating the user copy and edge tests.
 
## ADR-016: What-if sliders and synthetic shifts [DECISION] Date: 2026-10-27 Status: active
Context: The what-if mode must allow a user to change measurements and see the full pipeline respond, while the unusualness button should match the paper's stress recipe.
Options considered: Adjust a synthetic score directly; edit model outputs; or modify four real held-out features and send the complete row through predict_case, with a separate synthetic button for configured stress perturbations.
Decision and why: Start from a held-out test row, expose four of the six selected mean features as sliders, and recompute prediction/risk on each slider update. The button applies the configured signed 3-sigma shift to eight random features using TRAIN-fitted standard deviations, clips negatives to zero, and labels the profile synthetic. Seed, magnitude and feature count come from config.yaml.
Consequences / how to reverse: Slider and synthetic changes operate on data values only; they do not write inputs or directly set the decision. Any change to the stress recipe must update the seeded helper test and remain labeled synthetic.
