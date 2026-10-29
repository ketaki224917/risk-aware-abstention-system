# Master TODO

Status: `[ ]` todo, `[>]` doing, `[x]` done, `[!]` blocked, `[~]` dropped (with reason). Do not delete task IDs.

## Phase 0 Ã¢â‚¬â€ Foundations
- [x] P0.1 Inspect repo/ZIP; inventory existing files and identify reported-results path (none present; see ADR-001)
- [x] P0.2 Create `docs/state/*`; save the supplied master prompt as root `AGENTS.md`
- [x] P0.3 Create conventions, project metadata, uv lockfile, Makefile, lint and test setup
- [x] P0.4 Inspect legacy status and document absence of unrelated code in `legacy/README.md`
- [x] P0.5 Add config module and `config.yaml` for hyperparameters, weights, percentiles, seeds
- [x] P0.6 Record environment and obtain passing tests/lint smoke checks (GNU Make unavailable; direct commands passed)

## Phase 1 Ã¢â‚¬â€ Core pipeline
- [x] P1.1 Dataset loading and stratified 60/20/20 splitting with leakage tests
- [x] P1.2 RF-300 classifier and baseline metrics
- [x] P1.3 30-member bootstrap uncertainty and tests
- [x] P1.4 200-tree Isolation Forest anomaly score and tests
- [x] P1.5 Consequence module and ADR on values
- [x] P1.6 Validation-fitted normalization and weighted risk engine with tests
- [x] P1.7 Validation 70th/90th percentile policy with tests
- [x] P1.8 Single-case inference API and structured decision record

## Phase 2 Ã¢â‚¬â€ Explanations
- [x] P2.1 Immutable decision record schema
- [x] P2.2 Deterministic template explanation generator
- [x] P2.3 Rule-based explanation checker
- [x] P2.4 Fault injection and per-type detection evaluation
- [x] P2.5 Read-only explanation guarantee and test
- [x] P2.6 Optional exploratory local LLM adapter; it summarizes the fixed no-prediction status only, never changes inference, and remains unevaluated

## Phase 3 Ã¢â‚¬â€ Experiments
- [x] P3.1 Resumable 30-split pooled evaluation (3,420 test cases)
- [x] P3.2 Main results and paper reconciliation (source-aligned; result wording question recorded in BLOCKERS.md)
- [x] P3.3 Paired ablations
- [x] P3.4 Risk-coverage curve and percentile-pair sweep
- [x] P3.5 Uncertainty diagnostics, reliability, and ECE
- [x] P3.6 Synthetic anomaly stress test and policy behavior under shift
- [x] P3.7 Explanation checker evaluation
- [x] P3.8 Weight, consequence, and percentile sensitivity analyses
- [~] P3.9 Optional non-demographic proxy subgroup analysis (dropped; not needed for acceptance and not a fairness claim)
- [x] P3.10 End-to-end reproduction CLI generated all experiment artifacts; Make target could not be invoked because GNU Make is unavailable

## Phase 4 Ã¢â‚¬â€ App and documentation
- [x] P4.1 Demo app with three levels and clinical-use disclaimer (server health returned HTTP 200)
- [x] P4.2 Risk-by-level, risk-coverage, ablation, reliability, and stress ROC figures generated
- [x] P4.3 README with architecture, quickstart, source-aligned results, limitations, reported-results path
- [x] P4.4 Method, limitations, and results documentation
- [x] P4.5 Viva guide with walkthrough, 25 questions, and claim boundaries
- [ ] P4.6 Fresh-clone setup and reproduction remain unverified; GNU Make 4.4.1 make test, make lint, and make app pass in the active D: project.
- [!] P4.7 Final acceptance held for author review of paper-versus-run wording and the remaining fresh-clone setup/reproduction check.

## Phase 4.1 - User-facing demo replacement
- [x] P4.1a Inference API: `predict_case(features, measured_mask) -> DecisionRecord`
- [x] P4.1b Select six guided features by train-only importance and log ADR
- [x] P4.1c Fit partial-feature imputer on train only and log ADR
- [x] P4.1d Input validation, range/geometry warnings
- [x] P4.1e Held-out example-case selection and claim tests
- [x] P4.1f Example-first landing page
- [x] P4.1g Guided six-feature entry
- [x] P4.1h CSV upload/paste batch triage
- [x] P4.1i What-if controls and labeled synthetic stress recipe
- [x] P4.1j Exploratory review-capacity thresholds
- [x] P4.1k Why-abstain page sourced from results
- [x] P4.1l Accessible copy, glossary, safety language
- [x] P4.1m UI smoke and privacy tests
- [x] P4.1n README screenshots and 90-second viva script
- [~] P4.1o Guided-entry-first form (superseded by the requested questionnaire-first interface).
- [~] P4.1p Four-question, symptom-only intake returning Human Review (superseded by P4.1v report-feature model; no symptom-only class prediction).
- [~] P4.1q Train a model compatible with age, symptoms, family history, and medical history (no suitable symptom-only dataset; see DATA-001).
- [~] P4.1r Bright, responsive styling (superseded by the requested dark theme).
- [x] P4.1s Local LLM report, revised to report-only generation in P4.1x.
- [x] P4.1t Dark, high-contrast questionnaire; current form retains four symptom questions and compatible report inputs.
- [x] P4.1u IPv6 loopback binding for localhost.
- [x] P4.1v Add public UCI Mammographic Mass data and separate saved RAA model; fit preprocessing on TRAIN and record untouched seed-42 TEST metrics.
- [x] P4.1w Replace the default UI with a dark, plain-language questionnaire; use age and mammogram report fields, explain model sensitivity and route, and return Human Review when no report is available or report details are incomplete.
- [x] P4.1x Use local Ollama only after a user requests a report; keep result/routing deterministic and inputs in memory.
- [x] P4.1y Update README, method, results, limitations, viva guide, ADRs, blocker, and project handoff for the new scope.
- [x] P4.1z Restart localhost with the new app and verify HTTP health/root response, full tests, and lint.

- [x] P4.1aa Add requested height, weight, and gender questions; include answers in the user-requested local report while keeping unsupported fields out of the classifier.
