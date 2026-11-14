# Progress

### 2026-10-25 — P0.1 — Workspace inventory
Done: Inspected the workspace and confirmed it contains no source files, archive, paper, data, result outputs, or existing repository metadata. The reported-results path and legacy status therefore cannot be traced from existing artifacts.
Evidence: `Get-ChildItem -Force` and `rg --files --hidden` returned no files; `git status --short --branch` and `git log --oneline -20` failed with “not a git repository”.
Files: none (initial findings are carried into this state record and ADR-001).
Notes: No results are claimed as reproduced.

### 2026-10-25 — P0.2 — Session state and project prompt
Done: Created the `docs/state/` tracking files and copied the user-provided master prompt verbatim to root `AGENTS.md`.
Evidence: Initial read confirmed the prompt and state files were absent; attachment is saved as `AGENTS.md`.
Files: `AGENTS.md`, `docs/state/*`.
Notes: Session 1. Continue in TODO order.

### 2026-10-25 — P0.3 — Toolchain check (in progress)
Done: Checked available runtime commands and attempted the prescribed test entry point.
Evidence: `make test` failed because `make` is not recognized; `python --version` failed because `python` is not recognized; `py --version` reported no installed Pythons; `git --version` returned `2.55.0.windows.2`.
Files: `docs/state/ENVIRONMENT.md`, `docs/state/HANDOFF.md`.
Notes: Need a Python interpreter and a test runner before runtime verification. No numbers or model results have been produced.

### 2026-10-25 — P0.3 — Reproducible project scaffold
Done: Added Python package metadata, Makefile targets, Ruff/pytest configuration, and `uv.lock`.
Evidence: `uv lock --system-certs --python .tools/python-embed/python.exe` -> Resolved 57 packages; `uv sync --system-certs --all-groups --python .tools/python-embed/python.exe` -> installed 54 packages.
Files: `pyproject.toml`, `Makefile`, `uv.lock`, `.gitignore`.
Notes: GNU Make itself remains unavailable here; the Makefile commands are present and their uv equivalents were run directly.

### 2026-10-25 — P0.4 — Legacy inventory
Done: Confirmed no unrelated chest X-ray/ResNet-18 path was present; documented the empty quarantine.
Evidence: Initial `rg --files --hidden` returned no project files.
Files: `legacy/README.md`, `docs/state/DECISIONS.md`.
Notes: No user code was moved or deleted.

### 2026-10-25 — P0.5 — Configuration and explicit assumptions
Done: Centralized model sizes, seeds, risk weights, percentile thresholds, stress grid, consequence values, and evaluation settings.
Evidence: Loaded by the 30-split reproduction command; values are recorded in `config.yaml`.
Files: `src/raa/config.py`, `config.yaml`, `docs/state/DECISIONS.md`.
Notes: Consequence values 0/1 and 50 trees per bootstrap member are assumptions because no paper/source file was present.

### 2026-10-25 — P0.6 — Environment and smoke checks
Done: Created a workspace-local Python 3.13.17 environment, resolved/synced dependencies, and obtained passing tests and lint.
Evidence: `uv run python -m pytest -q` -> 12 passed; `uv run ruff check .` -> All checks passed. Direct commands used the local uv executable and `.tools/uv-cache`.
Files: `docs/state/ENVIRONMENT.md`, `uv.lock`.
Notes: GNU Make target invocation remains unverified because `make` is unavailable.

### 2026-10-25 — P1.1 — Dataset and leakage-safe split
Done: Added the sklearn dataset loader and stratified 60/20/20 index splitter with overlap checks.
Evidence: `pytest` passed; dataset test confirms 569 rows, 30 features, class counts 212/357, and partition sizes 341/114/114.
Files: `src/raa/data.py`, `tests/test_data.py`.

### 2026-10-25 — P1.2 — RF classifier and baseline
Done: Added RF-300 malignant probability inference and baseline metrics.
Evidence: Run `raa-20261025-01` pooled 3,420 test cases: error 4.064%, 85 false negatives, 54 false positives.
Files: `src/raa/models/classifier.py`, `src/raa/eval/metrics.py`, `results/runs/raa-20261025-01/metrics.json`.

### 2026-10-25 — P1.3 — Bootstrap uncertainty
Done: Added 30 bootstrap Random Forest members and population standard deviation of P(malignant).
Evidence: 30-split reproduction completed; uncertainty AUROC-for-errors split mean 0.891 (95% CI 0.864–0.915); 12 tests pass.
Files: `src/raa/models/uncertainty.py`, `src/raa/pipeline.py`.
Notes: 50 trees/member is an explicit assumption; disagreement is not a calibrated error probability.

### 2026-10-25 — P1.4 — Isolation Forest anomaly scoring
Done: Added training-only Isolation Forest with 200 trees and sign-correct anomaly scoring.
Evidence: 30-split and stress runs completed; synthetic-shift results are in `results/runs/raa-20261025-01/stress/`.
Files: `src/raa/models/anomaly.py`, `src/raa/eval/stress_test.py`.

### 2026-10-25 — P1.5 — Consequence assumption
Done: Added class consequence mapping and recorded its numeric assumption.
Evidence: Unit test confirms benign prediction gets the higher value; ADR-003 records that values are not clinical costs.
Files: `src/raa/models/consequence.py`, `config.yaml`, `docs/state/DECISIONS.md`.

### 2026-10-25 — P1.6 — Normalization and risk engine
Done: Added validation-fitted min-max ranges for U/A, clipping, and R=0.5U+0.2A+0.3C.
Evidence: Normalization/risk unit tests pass; full run uses validation-only component ranges.
Files: `src/raa/risk/normalization.py`, `src/raa/risk/engine.py`, `tests/test_risk_policy.py`.

### 2026-10-25 — P1.7 — Three-level policy
Done: Added validation percentile thresholds and exact routing boundary behavior.
Evidence: Threshold ordering and t70/t90 boundary tests pass; test partition never fits thresholds.
Files: `src/raa/risk/policy.py`, `tests/test_risk_policy.py`.

### 2026-10-25 — P1.8 — Inference API
Done: Added `DecisionSystem.predict` returning immutable structured records.
Evidence: Pipeline tests verify test-feature perturbations do not affect fitted validation thresholds and records carry bounded risk.
Files: `src/raa/pipeline.py`, `src/raa/explain/record.py`, `tests/test_pipeline.py`.

### 2026-10-25 — P2.1–P2.5 — Grounded explanations and checker
Done: Added immutable decision records, templates, rule checker, six fault types, and read-only guarantee tests.
Evidence: Explanation evaluation detected 12/12 injected faults and had 0/2 clean-template false positives; test suite passed 12 tests.
Files: `src/raa/explain/`, `src/raa/eval/explanation_eval.py`, `results/runs/raa-20261025-01/explanations/`.
Notes: Detection applies only to the enumerated faults/templates; no LLM path exists.

### 2026-10-25 — P3.1–P3.2 — Main 30-split results and reconciliation
Done: Ran all 30 seeds, each with 114 held-out test cases; cached each split and wrote pooled metrics and paper comparison.
Evidence: `uv run python -m raa.cli reproduce --run-id raa-20261025-01` -> 3,420 cases; pooled RF error 4.064%, full automatic coverage 68.538%, full automatic error 1.493%, false negatives routed away 77/85 (90.588%).
Files: `src/raa/eval/run_experiments.py`, `results/runs/raa-20261025-01/`, `docs/state/RECONCILIATION.md`.
Notes: Split cache identity includes config, source fingerprint, lockfile fingerprint, and Python version. Full-policy error target ≈0.70% is not supported; author wording/source details are open blockers.

### 2026-10-25 — P3.3–P3.5 — Ablation, coverage, uncertainty, calibration
Done: Added paired 7-way ablation, risk-coverage sweep, uncertainty AUROC/correlation, ECE, and reliability figure.
Evidence: uncertainty-only mean selective accuracy 99.301% (95% CI 98.973–99.597%) versus full 98.518% (98.106–98.942%); paired uncertainty-only minus full +0.783 pp (0.296–1.294 pp). ECE mean 0.0507 (0.0469–0.0547).
Files: `results/runs/raa-20261025-01/ablations.csv`, `risk_coverage.csv`, `diagnostics.csv`, `reliability.png`, `metrics.json`.
Notes: Negative finding is retained; no claim that every component improves accuracy.

### 2026-10-25 — P3.6 — Synthetic anomaly stress test
Done: Evaluated 3 feature subset sizes × 4 shift strengths, 2,000 paired case-bootstrap replicates per variant, and policy escalation rates.
Evidence: pooled AUROC over 12 variants 0.731 (paired case-bootstrap 95% CI 0.709–0.758); 10 features at 2σ AUROC 0.921 (0.882–0.957). Figures/tables in `results/runs/raa-20261025-01/stress/`.
Files: `src/raa/eval/stress_test.py`, `stress_test.csv`, `stress_policy.csv`, `stress_roc.png`.
Notes: Exact paper stress recipe was not provided, so pooled target comparison is recipe-dependent.

### 2026-10-25 — P3.7–P3.8 — Explanation evaluation and sensitivity
Done: Wrote checker detection metrics and predeclared weight, consequence, and percentile grids.
Evidence: Explanation checker 100% on 12 injected faults, 0% FPR on 2 clean examples; `sensitivity.csv` contains 27 weight settings, 9 consequence settings, and 8 ordered percentile pairs per split.
Files: `results/runs/raa-20261025-01/explanations/`, `sensitivity.csv`, `metrics.json`.
Notes: Fixed main configuration retained regardless of sensitivity results.

### 2026-10-25 — P3.10/P4.2 — End-to-end artifacts and visualizations
Done: Reproduction CLI generated main CSV/JSON/PNG outputs, anomaly stress outputs, checker outputs, and plots.
Evidence: Output includes `risk_by_level.png`, `risk_coverage.png`, `ablation_accuracy.png`, `reliability.png`, and `stress/stress_roc.png`.
Files: `results/runs/raa-20261025-01/`.

### 2026-10-25 — P4.1 — Demo application
Done: Added Streamlit sample picker, three route colors, decision record, grounded explanation, checker status, and persistent prototype disclaimer.
Evidence: Streamlit started on port 8765; `GET /_stcore/health` returned HTTP 200 `ok`.
Files: `src/raa/app/streamlit_app.py`, `Makefile`.

### 2026-10-25 — P4.3–P4.5 — Documentation package
Done: Added architecture/quickstart/results README, method, limitations, results, and viva guide with 25 questions and claim boundaries.
Evidence: All numerical statements are mapped to run `raa-20261025-01`; unsupported targets and assumptions are called out.
Files: `README.md`, `docs/method.md`, `docs/limitations.md`, `docs/results.md`, `docs/viva_guide.md`.

### 2026-10-25 — P4.6/P4.7 — Final acceptance status
Done: Recorded actual results and final blockers; implementation and equivalent checks are complete.
Evidence: 12 tests pass; Ruff clean; 30-split reproduction and app health check pass.
Files: `docs/state/TODO.md`, `docs/state/BLOCKERS.md`, `docs/state/HANDOFF.md`.
Notes: GNU Make was unavailable, so `make setup && make reproduce && make app` was not verified. Author must decide whether to revise unsupported claims and/or supply original paper/source details. Final acceptance remains pending.

### 2026-10-26 - Source-aligned paper review and reproduction
Done: Read the author's 16-page journal paper and five supplied background papers, mapped the evidence to project decisions, aligned implementation with specified values/scaling/stress protocol/seeds, and regenerated all result artifacts.
Evidence: `raa-20261026-paper-aligned-01` has 30 splits and 3,420 test rows; baseline errors match 142 (86 FN); automatic coverage is 70.41%; accepted errors are 13/2,408 (0.54%); baseline FN routed away are 73/86 (84.9%); Isolation Forest stress AUROC is 0.912 +/- 0.020; explanation checker detects 570/570 injected faults. Seed-42 baseline errors and Automatic count match the paper.
Files: `docs/state/SOURCE_MAP.md`, `docs/state/RECONCILIATION.md`, `docs/state/BLOCKERS.md`, `docs/method.md`, `docs/results.md`, `docs/limitations.md`, `README.md`, `config.yaml`, `src/raa/`, `results/runs/raa-20261026-paper-aligned-01/`.
Notes: Remaining differences are documented: exact full-policy accepted-error count, seed-42 Assisted/Human allocation and thresholds, and full-risk stress AUROC/escalation. RNG details are not fully specified in the paper. Pytest -> 12 passed; Ruff check -> all checks passed. GNU Make remains unavailable, so its literal targets are unverified.

### 2026-10-26 - Final source-alignment QA
Done: Rechecked lint, formatting, lock resolution, tests, Streamlit health, and generated figures; updated the run fingerprints and artifact inventory after the final CLI/plot changes.
Evidence: `ruff check .` passed; `ruff format --check .` found 53 formatted files; `pytest -q` reported 12 passed; `uv lock --check --offline` resolved 57 packages; Streamlit `/_stcore/health` returned HTTP 200 `ok`; `git diff --check` reported no whitespace errors. The ablation figure was visually reviewed after relabeling and switching error bars to split-level standard deviation.
Command: `uv run python -m raa.cli reproduce --run-id raa-20261026-paper-aligned-01` (executed with workspace-local uv and cache arguments as recorded in `metrics.json`).
Files: `results/runs/raa-20261026-paper-aligned-01/`, `src/raa/viz/plots.py`, `docs/state/ENVIRONMENT.md`, `docs/state/HANDOFF.md`.
Notes: `raa-20261025-paper-aligned-01` is retained as an earlier intermediate run; the canonical comparison and final project results use `raa-20261026-paper-aligned-01`.

### 2026-10-26 - Commit source-alignment work
Done: Committed the source-aligned code, documentation, and run artifacts; tagged the completed experiments phase.
Evidence: Commit `d2f0b78` (`[P3.2] Align RAA with supplied journal paper`); tag `phase-3-done`; `git status --short --branch` was clean after commit.
Files: All project changes for the 2026-10-26 source-alignment task.
Notes: Elevated Git required a command-scoped safe-directory setting and the prior project identity `Codex <codex@localhost>`; no global Git configuration was changed.

### 2026-10-27 - P4.6/P4.7 - Relocate project and verify D: environment
Done: Reconstructed the complete tracked worktree at `D:\ERA CP`, created a fresh locked `.venv`, and ran the project smoke checks there. The old C: source folder remains as a backup because Windows denied deletion of `.git\hooks` during the cross-volume move; no ACLs were changed.
Evidence: `uv --system-certs --cache-dir .tools/uv-cache sync --all-groups --locked` -> 57 resolved, 54 checked; `uv --cache-dir .tools/uv-cache run pytest -q` -> 12 passed; Ruff check passed; offline lock check resolved 57 packages; Streamlit health returned HTTP 200 `ok`; Git worktree clean.
Files: D: project files and `docs/state/`.
Notes: A literal MinGW Make 3.82.90 dry run fails with `INTERNAL: readdir: Invalid argument`; equivalent uv checks pass. The existing canonical 30-split run remains valid. A duplicate rerun was stopped at the user's request to relocate the project, and its touched cache files were restored from Git. `CLAIM-001` still needs author wording review.
### 2026-10-27 - P4.1a - Thin case inference API
Done: Added `predict_case(features, measured_mask, context=...)` in `src/raa/inference.py`. The adapter validates the measured vector/mask, supports a pre-fitted train-only KNN imputer for partial vectors, calls the existing `DecisionSystem.predict`, and annotates the immutable `DecisionRecord` with measured/estimated counts and warnings.
Evidence: `uv --cache-dir .tools/uv-cache run pytest -q tests/test_inference.py` -> 1 passed; focused Ruff check -> all checks passed. The regression test compares the adapter output with the real pipeline for a fixed held-out row.
Files: `src/raa/inference.py`, `src/raa/explain/record.py`, `tests/test_inference.py`, `docs/state/DECISIONS.md`.
Notes: UI integration and additional validation/imputation tests remain in P4.1c/d. The existing app file is still WIP and will be replaced in later app tasks.

### 2026-10-27 - P4.1b - Train-only guided feature selection
Done: Added a deterministic selector that ranks the ten mean WDBC features by the fixed seed-42 TRAIN-fitted Random Forest importances and returns the top six. ADR-011 records the measured ranking; non-mean fields are never eligible.
Evidence: `uv --cache-dir .tools/uv-cache run pytest -q tests/test_inference.py` -> 2 passed; focused Ruff -> all checks passed. Importance command: loaded WDBC, created the seed-42 stratified split, and called `fit_system(..., split.train, split.validation, ..., seed=42)`; top six mean importance values are recorded in ADR-011.
Files: `src/raa/inference.py`, `tests/test_inference.py`, `docs/state/DECISIONS.md`.

### 2026-10-27 - P4.1c - Train-only partial input imputation
Done: Implemented distance-weighted five-neighbor KNN imputation in `InferenceContext.fit_from_training`, which also derives observed feature bounds from the same supplied TRAIN rows. Partial predictions run the real fitted decision system and include six-of-30 measured/estimated metadata plus an imputation caveat.
Evidence: `uv --cache-dir .tools/uv-cache run pytest -q tests/test_inference.py` -> 3 passed. The new test confirms the imputer's stored fit matrix and min/max equal only the seed-42 TRAIN partition; a six-feature row returns a finite risk and 6/24 counts.
Files: `src/raa/inference.py`, `tests/test_inference.py`, `docs/state/DECISIONS.md`.

### 2026-10-27 - P4.1d - Friendly input validation and plausibility warnings
Done: Confirmed invalid measured values are rejected with field-specific messages; out-of-training-range measurements and large radius/perimeter/area circle-check differences produce non-blocking warnings. ADR-013 records the 50% approximate geometry tolerance and warning-only policy.
Evidence: `uv --cache-dir .tools/uv-cache run pytest -q tests/test_inference.py` -> 5 passed; focused Ruff -> all checks passed. Cases cover nonnumeric, NaN, infinity, negative, vector/mask shape, range and geometry.
Files: `src/raa/inference.py`, `tests/test_inference.py`, `docs/state/DECISIONS.md`.

### 2026-10-27 - P4.1e - Verified held-out examples and saved demo model
Done: Added six unique example cards: lowest-risk Automatic, highest-risk Human Review, borderline just above validation-p90, top-decile anomaly, classifier baseline error, and deterministic random held-out row. Added an offline artifact builder and a loader that cannot refit, plus a Make target that only prepares the artifact when missing.
Evidence: `uv --cache-dir .tools/uv-cache run python -m raa.app.prepare_demo_artifact` created a 1,308,233-byte seed-42 model bundle from 341 train / 114 validation / 114 test rows, plus `manifest.json`, `feature_importance.csv`, and `example_cases.json`. `pytest -q tests/test_examples.py` -> 2 passed; category tests verify the claims against actual held-out predictions and recorded WDBC targets; test monkeypatches fit to fail during loading.
Files: `src/raa/app/demo_assets.py`, `src/raa/app/examples.py`, `src/raa/app/prepare_demo_artifact.py`, `Makefile`, `tests/test_examples.py`, `results/demo/`.

### 2026-10-27 - P4.1f - Example-first landing page
Done: Replaced the incomplete sample picker with a Mode A landing page that offers six one-click held-out cases and an optional recorded-label reveal. The shared result renderer shows icon plus text, model-lean wording, three signal bars, risk thresholds/gauge, measured count, checked template explanation, glossary, method/limits, and a permanent non-diagnosis banner. The page loads the saved artifact and never trains.
Evidence: `uv --cache-dir .tools/uv-cache run pytest -q tests/test_ui.py` -> 1 passed; AppTest opened a case in one click and checked the banner; focused Ruff passed. Aggregate Why abstain values read `results/runs/raa-20261026-paper-aligned-01/metrics.json`.
Files: `src/raa/app/streamlit_app.py`, `src/raa/app/copy.py`, `tests/test_ui.py`.
 
### 2026-10-27 - P4.1g - Six-field guided entry
Done: Added six data-driven mean-feature controls, each with a slider and exact-number box. Controls show TRAIN p5-p95 typical ranges and allow out-of-range numeric values for explicit warning. Submission fills only six measured fields, imputes the remaining 24 using the saved TRAIN-only KNN model, then calls predict_case and the complete RAA pipeline.
Evidence: uv --cache-dir .tools/uv-cache run pytest -q tests/test_ui.py -> 2 passed; Mode B AppTest confirms exactly six sliders and number inputs and checks the displayed 6/24 note after prediction. Inference tests confirm estimated counts and real pipeline risk. Ruff passed.
Files: src/raa/app/streamlit_app.py, tests/test_ui.py.
 
### 2026-10-27 - P4.1h - CSV batch triage
Done: Added an empty 30-feature template download, CSV paste/upload, exact-header validation, 100-row limit, friendly errors, in-memory batch inference, triage table, tier percentages, and results download. The generated output does not repeat measured feature values.
Evidence: pytest tests/test_batch.py tests/test_ui.py -> 5 passed; focused Ruff passed. Batch tests cover template headers, valid real pipeline inference, empty/missing columns, blank feature, row limit, and no disk writes to a temporary directory. AppTest confirms pasted CSV yields one triage row and three tier metrics.
Files: src/raa/inference.py, src/raa/app/streamlit_app.py, tests/test_batch.py, tests/test_ui.py, docs/state/DECISIONS.md.
 
### 2026-10-27 - P4.1i - Live what-if and synthetic unusualness
Done: Added four sliders on a held-out test profile; each slider change recomputes the model lean, uncertainty, anomaly, consequence, risk, policy and explanation. The synthetic button applies the configured signed 3-sigma shift to eight features using TRAIN standard deviations, clips to zero, and identifies the changed features and synthetic status.
Evidence: pytest tests/test_stress_input.py tests/test_ui.py -> 5 passed. The stress test verifies determinism, eight changed features, sign directions and clipping. AppTest verifies a slider adjustment changes the displayed risk score and that the synthetic button labels the result. Ruff passed.
Files: src/raa/inference.py, src/raa/app/streamlit_app.py, tests/test_stress_input.py, tests/test_ui.py, docs/state/DECISIONS.md.
 
### 2026-10-27 - P4.1j - Exploratory review capacity
Done: Versioned the demo bundle and saved its 114 validation risk values under results/demo. Added a collapsed capacity control that maps c cases per 100 to validation percentiles (Automatic p100-c; Human Review cutoff p100-c/3), preserving p70/p90 at the default 30/100. Route changes apply only to the current display.
Evidence: pytest tests/test_review_capacity.py tests/test_ui.py tests/test_examples.py -> 7 passed; focused Ruff passed. API tests verify exact default thresholds, changed p80/p93.33 cutoffs, unchanged input risk/class, and byte-identical canonical metrics. AppTest verifies the default mapping and changed capacity display.
Files: src/raa/app/demo_assets.py, src/raa/inference.py, src/raa/app/streamlit_app.py, results/demo/model_bundle.joblib, results/demo/manifest.json, results/demo/validation_risk.csv, tests/test_review_capacity.py, tests/test_ui.py.
 
### 2026-10-27 - P4.1k - Results-backed Why abstain page
Done: Added dedicated checks for the Why abstain page, which reads canonical pooled metrics from results/runs/raa-20261026-paper-aligned-01/metrics.json and displays run ID, baseline error, automatic coverage, tier errors, and false-negative routing.
Evidence: pytest tests/test_results_page.py -> 1 passed; test parses source JSON and compares displayed values; focused Ruff passed.
Files: src/raa/app/streamlit_app.py, src/raa/app/demo_assets.py, tests/test_results_page.py.
 
### 2026-10-27 - P4.1l - Accessible, safety-bounded interface copy
Done: Centralized UI copy in app/copy.py, removed corrupted UTF-8 text, retained the permanent exact prototype/non-diagnosis banner, added plain-language glossary definitions, and marked risk thresholds both visually and textually with ARIA values. Route output always pairs a traffic-light icon with a textual tier and “the model leans” wording.
Evidence: tests/test_copy_a11y.py and tests/test_ui.py -> 7 passed; Ruff check . -> all checks passed. AppTest checks route text, explanation checker status, the risk-gauge ARIA label, and banner persistence across all five modes.
Files: src/raa/app/copy.py, src/raa/app/streamlit_app.py, tests/test_copy_a11y.py, tests/test_ui.py, docs/state/DECISIONS.md.
 
### 2026-10-27 - P4.1m - UI, input and privacy test coverage
Done: Completed direct validation tests for nonnumeric, NaN/infinite, negative, shape, range and geometry cases; imputer/train-only checks; full/partial real-pipeline parity; held-out example claims; CSV template, invalid schemas, personal ID columns, blank values and row limits; explanation read-only guarantee; all five UI modes and permanent banner. Batch tests check no files appear in a temporary output directory, and AppTest confirms demo artifacts do not change during CSV handling.
Evidence: pytest tests/test_batch.py tests/test_ui.py tests/test_explanation.py tests/test_copy_a11y.py -> 16 passed; focused Ruff passed.
Files: tests/test_batch.py, tests/test_ui.py.

### 2026-10-27 - P4.1n - README screenshot and 90-second viva walkthrough
Done: Replaced the stale four-section input description with the example-first five-mode guide, local startup instructions, saved-artifact provenance, risk/output explanation, privacy limits, run results, pipeline diagram, and 90-second viva walkthrough. Saved a real 1280x672 screenshot of the running landing page at docs/images/raa-demo.jpg. Fixed make app startup after a clean Streamlit profile prompted for an email: the app target now uses headless mode and disables Streamlit usage statistics; ADR-019 records this choice.
Evidence: make test -> 35 passed; make lint -> all checks passed; uv --cache-dir .tools/uv-cache run ruff format --check . -> 66 files already formatted; uv --cache-dir .tools/uv-cache lock --check --offline -> 57 packages resolved; make app -> Local URL http://localhost:8501; GET /_stcore/health -> HTTP 200, ok.
Files: README.md, docs/images/raa-demo.jpg, Makefile, docs/state/DECISIONS.md, docs/state/BLOCKERS.md, docs/state/ENVIRONMENT.md, docs/state/TODO.md, docs/state/PROGRESS.md, docs/state/HANDOFF.md, src/raa/explain/record.py.
Notes: GNU Make 4.4.1 at D:/msys64/usr/bin/make.exe is now used; the old MinGW make remains defective but is not the resolved make command. Fresh-clone setup and reproduction remain unverified. CLAIM-001 author wording review remains open.

### 2026-10-27 - P4.1q - Evaluate a questionnaire-compatible dataset candidate
Done: Added the public Duke BRCA table and an offline feasibility audit. The table contains age bands, family history, prior breast biopsy/surgery, and a symptom field limited to lump/nipple discharge. The app was not connected to this candidate because its label is historical screening follow-up and held-out performance failed the feasibility check.
Evidence: `python scripts/audit_questionnaire_dataset.py` with the locked project dependencies and seed 42; one stratified 60/20/20 split gave 591 TRAIN, 198 VALIDATION, 198 TEST; 37/987 cancer outcomes overall and 7 in TEST. Full RAA pipeline: `class_weight=balanced_subsample`, RF-300, 30 bootstrap RF-50 members, Isolation Forest-200, validation p70/p90. TEST sensitivity 0/7, specificity 168/191 (87.96%), ROC-AUC 0.486537. Metrics: `results/clinical_candidate_audit/metrics.json`.
Files: `data/brca.txt`, `data/README.md`, `scripts/audit_questionnaire_dataset.py`, `results/clinical_candidate_audit/metrics.json`, class-weight option in classifier/uncertainty/pipeline, `docs/state/DECISIONS.md`, `docs/state/BLOCKERS.md`.
Notes: DATA-001 stays open. The app must not show this candidate's predicted class or Automatic/Assisted route for user answers. The current form's Human Review/no-prediction behavior remains until a suitable dataset is available.


### 2026-10-27 - P4.1r - Bright, responsive intake styling
Done: Added a light blue-and-white page theme, clearer focus outlines, rounded form cards and buttons, and a mobile-width layout. Kept the research-prototype/non-diagnosis notice visible as a warning banner. Questionnaire answers still do not feed the incompatible WDBC model.
Evidence: source-level review of the intake page; no test or browser run was performed for this CSS-only change.
Files: src/raa/app/streamlit_app.py.


### 2026-10-28 - P4.1s - Local LLM status report and app recovery
Done: Added a local-only Ollama adapter using qwen2.5:1.5b by default. It receives only fixed no-prediction status facts, validates the returned wording, and cannot alter inference. The intake now offers a user-triggered plain-text report; report data is created in memory and includes answers only on download. The app was restarted on its local-only address.
Evidence: a focused local call using synthetic status text returned a Human Review/no-class-estimate summary; a synthetic report check confirmed answer fields, no-prediction outcome, and the local-only privacy statement. Ruff check passed; Ruff format check passed; git diff --check passed. Direct Streamlit launch returned HTTP 200 for both /_stcore/health and /, with health body "ok". A focused Streamlit AppTest with synthetic answers verified the Human Review result, local LLM summary, and report download button. No full pytest suite was run in this task.
Files: src/raa/explain/llm_adapter.py, src/raa/app/report.py, src/raa/app/streamlit_app.py, src/raa/app/copy.py, README.md, docs/state/*.
Notes: Local Ollama API docs use POST /api/chat with stream=false for a complete response: https://github.com/ollama/ollama/blob/main/docs/api.md. The LLM is exploratory and not evaluated. The questionnaire classifier remains blocked under DATA-001.


### 2026-10-28 - P4.1t - Dark, high-contrast expanded questionnaire
Done: Switched Streamlit's configured theme to dark and applied explicit high-contrast colors to page text, labels, alerts, fields, buttons, and keyboard focus. The intake now asks five basic items (age, height, weight, gender, breast/family history) and four separate symptom questions. The report includes all answers only when downloaded; neither the classifier nor local LLM receives them.
Evidence: focused Streamlit AppTest with synthetic answers verified the nine inputs, Human Review/no-prediction output, local LLM explanation, and report download button. Ruff check and formatting passed. The computer-use browser surface was unavailable, so no screenshot-based inspection was possible. After restarting with the new theme, /_stcore/health returned HTTP 200 with body ok and / returned HTTP 200.
Files: .streamlit/config.toml, src/raa/app/streamlit_app.py, src/raa/app/copy.py, src/raa/app/report.py, tests/test_ui.py, README.md, docs/state/*.
Notes: P4.1q remains blocked. This UI change does not train a cancer classifier.


### 2026-10-28 - P4.1u - Fix localhost IPv6 binding
Done: Diagnosed that Streamlit accepted IPv4 only while localhost resolves to IPv6 ::1 on this machine. Changed the app target to bind exclusively to IPv6 loopback and updated the README.
Evidence: netstat showed [::1]:8501 LISTENING. HTTP checks returned 200 for http://localhost:8501/, http://[::1]:8501/, and health at http://[::1]:8501/_stcore/health. Direct IPv4 http://127.0.0.1:8501/ is unavailable by design.
Files: Makefile, README.md, docs/state/DECISIONS.md, docs/state/ENVIRONMENT.md, docs/state/HANDOFF.md, docs/state/TODO.md.
Notes: Binding remains local-only. The app server is currently started in the background.


### 2026-10-29 - P4.1v-y - Report-based app model, interface, and report flow
Done: Added the public UCI Mammographic Mass data and a separate saved RAA model using age and mammogram report shape, margin, and density. Replaced the Human Review-only landing screen with the dark questionnaire and an honest mass-label estimate; no report means Human Review/no class estimate and incomplete report fields force Human Review. The local Ollama writer runs only after a report request. Updated documentation, added the dataset/model ADR, and preserved the original Wisconsin paper experiment and its artifacts.
Evidence: `make mammography-artifact` built `results/mammographic_mass/model_bundle.joblib` from 576 TRAIN rows with imputation/encoding fit on TRAIN, route thresholds fit on validation, and metrics on a held-out TEST of 193. TEST accuracy 73.1%, malignant sensitivity 61.8%, benign specificity 82.7%, malignant AUROC 0.810; p70/p90 Automatic error 20.0% (26/130). `make test` -> 42 passed; `make lint` -> all checks passed; `ruff format --check .` -> 75 files formatted.
Files: UCI source files, `src/raa/mammography.py`, app and report modules, `results/mammographic_mass/`, tests, README and research documentation/state.

### 2026-10-29 - P4.1aa - Complete basic health inputs and requested report
Done: Added height, weight, and gender alongside age, family/medical history, and the four symptom questions. The fields appear in the requested in-memory report and are provided to the local LLM only after the report button is selected. Only age plus mammogram report shape, margin, and density affect the saved model and RAA pipeline; the unsupported answers stay context-only.
Evidence: `make test` -> 42 passed; `make lint` -> all checks passed; `ruff format --check .` -> 75 files already formatted. The app tests cover the revised field counts, report context, model output, and privacy.
Files: `src/raa/app/health_intake.py`, `src/raa/app/copy.py`, `src/raa/app/report.py`, `src/raa/explain/llm_adapter.py`, `tests/test_ui.py`, `tests/test_report.py`, `tests/test_results_page.py`, README and state documentation.


### 2026-10-29 - P4.1z - Restart and verify updated localhost app
Done: Stopped the previously running Streamlit process only after confirming its command line, then relaunched the updated app hidden and bound exclusively to IPv6 loopback.
Evidence: `http://localhost:8501/` -> HTTP 200; `http://[::1]:8501/_stcore/health` -> HTTP 200 with body `ok`; current landing page and updated question counts are covered by Streamlit AppTest. Full regression: `make test` -> 42 passed; `make lint` -> all checks passed.
Files: Makefile launch target is unchanged; the updated app and state files are included in this task.


### 2026-10-29 - P4.1ab - Generate downloadable Word prediction reports
Done: Added a standard-library OOXML writer that turns the requested report into a formatted `.docx` in memory. The download includes the dynamic class/route, local LLM summary, model-sensitivity explanation, all entered answers, held-out metrics, and model limits. Word tables have repeated header rows. The app continues to create the report only after the user requests it and does not save it automatically.
Evidence: `make test` -> 42 passed; `make lint` -> all checks passed; `ruff format --check .` -> 76 files formatted; `git diff --check` passed. A temporary Word preview generated from a public held-out UCI record was accepted by Microsoft Word and exported to a two-page PDF; the Word-exported HTML preview was visually inspected, and PDF extraction confirmed the input table header repeats on page two. ZIP integrity, XML parsing, report fields, and all three repeat-header rows are covered by `tests/test_report.py`. The canonical `render_docx.py` attempt found `pdf2image` and LibreOffice are unavailable, so QA used the installed Word renderer instead.
Files: `src/raa/app/docx_report.py`, `src/raa/app/health_intake.py`, `tests/test_report.py`, `tests/test_ui.py`, `README.md`, and state documentation.


### 2026-10-29 - P4.1ac - Serve the Word report update locally
Done: Restarted Streamlit after adding DOCX download and confirmed it still binds only to IPv6 loopback.
Evidence: `http://localhost:8501/` -> HTTP 200; `http://localhost:8501/_stcore/health` -> HTTP 200 with body `ok`; current app root is served by the updated D: project.
Files: app runtime only; launch configuration continues to use `::1`.

### 2026-11-14 — P4.1ad — Audit questionnaire-compatible dataset candidate
Done: Downloaded the official BrEaST clinical metadata workbook to D:, preserved it with its CC BY 4.0 source details, and added a reproducible schema/completeness audit. The candidate is not connected to user inference because it does not match the intake fields and has substantial missingness. No synthetic labels were created.
Evidence: `python scripts/audit_breast_symptom_candidate.py` → 256 rows (154 benign, 98 malignant, 4 normal); among 252 binary-label rows, age missing 41, Signs missing 45, Symptoms missing 94; 132 complete rows (76 benign, 56 malignant). Direct saved-model check on two compatible report inputs returned benign (score 0.180) and malignant (score 0.918); the in-memory Word report contained the matching result and passed ZIP/XML checks (4,296 bytes). A focused pytest attempt could not run because the D:-only embedded Python has no pytest installed; the existing project venv points to an inaccessible C: Python, so no C: runtime was used.
Files: `data/breast_lesions_usg_clinical.xlsx`, `data/README.md`, `scripts/audit_breast_symptom_candidate.py`, `results/br_east_candidate_audit/audit.json`, `README.md`, and state files.
Notes: The current app remains dynamic when mammogram report features are supplied. General health answers alone intentionally return Human Review because the saved classifier was not trained on them. DOCX generation remains per user submission.
### 2026-11-14 — P4.1af — Reproduce Human Review routing
Done: Reproduced the user-facing form with complete mammogram report fields using Streamlit AppTest. The app returned Automatic with a benign model lean and no exceptions. Human Review is expected when no report is supplied or a report field is Not sure; symptom answers are context only.
Evidence: D:-only AppTest smoke script at D:\Temp\raa-app-runtime\apptest_complete_input.py -> Automatic - the model leans benign; exceptions: 0. The localhost health endpoint remained HTTP 200.
Files: project state only; no user-facing code changed.
