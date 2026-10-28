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
 
## ADR-017: Map exploratory team capacity to validation percentiles [DECISION] Date: 2026-10-27 Status: active
Context: A review team needs to explore referral thresholds at a capacity other than the paper's default, without changing reported experiment values.
Options considered: Change the model risk score; hard-code a route by capacity; or select cutoffs from the saved seed-42 validation-risk distribution while preserving the default operating point.
Decision and why: For capacity c cases per 100, set the Automatic cutoff at validation percentile 100-c and the Human Review cutoff at 100-c/3. This allocates two-thirds of review capacity to Assisted and one-third to the highest-risk Human Review tier. At c=30, the mapping exactly returns p70/p90. Capacity is adjustable only in a collapsed exploratory expander and is not written back to canonical metrics.
Consequences / how to reverse: Validation risk scores are saved in results/demo/validation_risk.csv and the saved model bundle. Ties in a finite validation set can make realized routing counts differ slightly from the requested percentage. Any different capacity mapping must preserve the 70/90 default or explicitly document the change.
 
## ADR-018: Make route and risk visuals independent of color [DECISION] Date: 2026-10-27 Status: active
Context: The traffic-light routing output and risk gauge must remain understandable with color vision differences and assistive technology.
Options considered: Use green/yellow/red styling alone; display icons alone; or pair each route icon with its text and expose the numeric risk thresholds in text and an ARIA-labeled gauge.
Decision and why: Render each route with an icon plus the explicit Automatic/Assisted/Human Review label and “model leans” phrasing. The risk bar includes visible dark threshold marks, a numeric text summary, and an ARIA label with score/cutoffs. Signal bars have text labels and numeric values. Glossary/help copy describes each signal and its limits.
Consequences / how to reverse: Keep route text, gauge text and ARIA values synchronized when changing UI styling or route labels.

## ADR-019: Make local app startup noninteractive and telemetry-free [DECISION] Date: 2026-10-27 Status: active
Context: The first actual make app launch on a clean Streamlit profile prompted for an activation email and exited with error 127 when run without interactive stdin. A user case-input demo should launch without requesting personal details or opening a browser automatically.
Options considered: Require a user email; commit a local Streamlit credential/config file; or pass headless and usage-stat settings on the app command.
Decision and why: The Makefile app recipe passes --server.headless=true --browser.gatherUsageStats=false. Headless mode skips the activation prompt and browser auto-open; disabling usage statistics also suppresses the first-run telemetry message.
Consequences / how to reverse: make app starts the local server without collecting an email or sending Streamlit usage statistics. This does not change case inference or saved experiment results. Reconsider only if the demo intentionally adopts an interactive Streamlit setup flow.

## ADR-020: Keep the four-question intake outside the WDBC model [DECISION] Date: 2026-10-27 Status: active
Context: The requested default interface collects age, symptoms, family history, and medical history, while the existing Random Forest was trained on 30 numeric cell-nucleus features from WDBC. No compatible labeled dataset for the four intake fields is present.
Options considered: Map the answers to WDBC features or invent a Malignant/Benign result; keep the WDBC example page as the landing page; or collect the four answers and clearly abstain without loading or calling the incompatible model.
Decision and why: Make the four-question form the landing page. Require an age from 1 to 120 and explicit selections for the three categorical questions. On submission, show “Human Review — no prediction made” and explain that no medical assessment, referral, or diagnosis was produced. Do not pass these fields to the WDBC pipeline. Keep WDBC guided entry, CSV, what-if, examples, and results pages as optional research modes. A future Malignant/Benign classifier requires compatible labeled data and separately documented training and validation.
Privacy: Do not persist intake answers. Bind the app server to 127.0.0.1 so submitted values are available only through the local demo by default.
Consequences / how to reverse: The UI cannot produce a malignant or benign result from these four answers until a compatible model is built and validated. Dataset availability, data handling, and validation scope must be addressed in a superseding ADR before enabling predictions.

## ADR-021: Reject the Duke BRCA table as a questionnaire classifier [DECISION] Date: 2026-10-27 Status: active
Context: The user asked to replace WDBC's cell measurements with age, symptoms, family history, and prior breast history. Duke's public BRCA screening table appears to contain corresponding fields, but its label is a diagnosis recorded within 12 months of a 2002 screening mammogram, not current malignant/benign pathology.
Evidence: The official Duke page documents 987 records and a binary 12-month follow-up outcome. Parsing the downloaded file yielded 37 cancer outcomes and 950 without a recorded cancer outcome. With seed 42 and stratified 60/20/20 splitting (591/198/198), the full RAA pipeline used 300-tree Random Forest with `balanced_subsample`, 30 bootstrap members of 50 trees, training-fitted Isolation Forest-200, and validation p70/p90 thresholds. On the untouched 198-row TEST partition (7 cancer outcomes), sensitivity was 0/7, specificity 168/191 (87.96%), and ROC-AUC 0.4865.
Decision and why: Keep the source file only as an evaluated candidate. Do not connect its model or outputs to user intake. Do not relabel the follow-up outcome as Malignant/Benign and do not claim the prototype detects cancer. The data's small positive count and poor held-out discrimination make its predictions unsuitable even as a useful questionnaire demo.
Consequences / how to reverse: DATA-001 remains open. A new compatible, adequately sized, approved dataset and independent validation are required before displaying predicted classes or automatic/assisted routing for these answers. Metrics from this audit belong only to `results/clinical_candidate_audit/metrics.json` and must not replace the WDBC paper-reproduction results.


## ADR-022: Keep the LLM status summary local and read-only [DECISION] Date: 2026-10-28 Status: active
Context: The user requested an LLM and a downloadable report. The four-question intake is not connected to a compatible cancer classifier, so the system has no class prediction to explain. Questionnaire answers are sensitive and should not be sent to a hosted model without explicit authorization.
Options considered: Send answers to a hosted LLM; ask a local LLM to interpret the answers; or use a local LLM only to rephrase a fixed Human Review/no-prediction status and build the report deterministically.
Decision and why: Use the Ollama API at 127.0.0.1:11434 with qwen2.5:1.5b by default. The LLM prompt contains only fixed status facts; no answers or WDBC features are accepted by its adapter. Accept only short output that explicitly preserves Human Review/no prediction and rejects disease, diagnosis, treatment, recommendation, or risk claims. If Ollama is unavailable or output fails the safety gate, use a fixed explanation. Keep the route and class result deterministic. Build the report in memory and offer it only as a user-triggered text download.
Consequences / how to reverse: This is an exploratory wording aid, not a validated explanation model, and it cannot produce Malignant/Benign predictions. The report contains answers only when downloaded by the user. A future remote provider or prediction model requires a superseding ADR, explicit data handling review, compatible labeled data, and separate evaluation.


## ADR-023: Collect the requested questionnaire fields locally [DECISION] Date: 2026-10-28 Status: active
Context: The user asked for age, height, weight, gender, and four separate symptom questions. ADR-020 specified no demographic input because the previous requested intake contained only four fields. The model still has no compatible training data for any of these answers.
Options considered: Ignore the latest requested fields; pass them to the WDBC classifier or LLM; or collect the requested fields in the local interface and report without using them for prediction.
Decision and why: Collect five basic fields (age, height, weight, gender, and one breast/family-history question) plus separate Yes/No/Not sure answers for lump, breast swelling, skin changes, and nipple changes. This supersedes ADR-020 only for the displayed intake fields. Keep all fields in the local Streamlit session; do not pass them to the classifier or LLM. Include them in the report only after the user chooses to download it. Continue returning Human Review with no predicted class.
Consequences / how to reverse: The form includes demographic and health details at the user's direct request. The app does not persist them by default or send them to an external service. They provide no evidence for a cancer estimate and must not change the route. A suitable labeled dataset and independent validation remain necessary for predictions.


## ADR-024: Bind the local app to IPv6 loopback [DECISION] Date: 2026-10-28 Status: active
Context: The app was bound only to IPv4 127.0.0.1. On this Windows machine, localhost resolves to both ::1 and 127.0.0.1; an IPv6-only connection to ::1 failed even though the IPv4 page returned HTTP 200.
Options considered: Keep the IPv4-only bind and ask the user to choose an IP URL; bind to all interfaces; or bind specifically to IPv6 loopback so browsers that resolve localhost to ::1 can connect while the app remains local-only.
Decision and why: Use --server.address=::1 in Makefile and startup instructions. Verification showed http://localhost:8501 and http://[::1]:8501 return HTTP 200. Do not bind to 0.0.0.0 or a LAN address.
Consequences / how to reverse: Use http://localhost:8501 as the app URL. Direct IPv4 127.0.0.1 is not a listener. Revisit only if the target machine lacks IPv6 loopback; any replacement must remain bound to loopback.
