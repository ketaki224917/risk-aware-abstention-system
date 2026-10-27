# Master TODO

Status: `[ ]` todo, `[>]` doing, `[x]` done, `[!]` blocked, `[~]` dropped (with reason). Do not delete task IDs.

## Phase 0 â€” Foundations
- [x] P0.1 Inspect repo/ZIP; inventory existing files and identify reported-results path (none present; see ADR-001)
- [x] P0.2 Create `docs/state/*`; save the supplied master prompt as root `AGENTS.md`
- [x] P0.3 Create conventions, project metadata, uv lockfile, Makefile, lint and test setup
- [x] P0.4 Inspect legacy status and document absence of unrelated code in `legacy/README.md`
- [x] P0.5 Add config module and `config.yaml` for hyperparameters, weights, percentiles, seeds
- [x] P0.6 Record environment and obtain passing tests/lint smoke checks (GNU Make unavailable; direct commands passed)

## Phase 1 â€” Core pipeline
- [x] P1.1 Dataset loading and stratified 60/20/20 splitting with leakage tests
- [x] P1.2 RF-300 classifier and baseline metrics
- [x] P1.3 30-member bootstrap uncertainty and tests
- [x] P1.4 200-tree Isolation Forest anomaly score and tests
- [x] P1.5 Consequence module and ADR on values
- [x] P1.6 Validation-fitted normalization and weighted risk engine with tests
- [x] P1.7 Validation 70th/90th percentile policy with tests
- [x] P1.8 Single-case inference API and structured decision record

## Phase 2 â€” Explanations
- [x] P2.1 Immutable decision record schema
- [x] P2.2 Deterministic template explanation generator
- [x] P2.3 Rule-based explanation checker
- [x] P2.4 Fault injection and per-type detection evaluation
- [x] P2.5 Read-only explanation guarantee and test
- [~] P2.6 Optional exploratory LLM adapter (dropped: templates satisfy scope; no unevaluated LLM path)

## Phase 3 â€” Experiments
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

## Phase 4 â€” App and documentation
- [x] P4.1 Demo app with three levels and clinical-use disclaimer (server health returned HTTP 200)
- [x] P4.2 Risk-by-level, risk-coverage, ablation, reliability, and stress ROC figures generated
- [x] P4.3 README with architecture, quickstart, source-aligned results, limitations, reported-results path
- [x] P4.4 Method, limitations, and results documentation
- [x] P4.5 Viva guide with walkthrough, 25 questions, and claim boundaries
- [!] P4.6 Fresh-environment `make setup && make reproduce && make app` not verified; GNU Make is unavailable in this environment
- [!] P4.7 Final acceptance held for author review of run-vs-paper differences and direct Make-target verification

## Phase 4.1 - User-facing demo replacement
- [x] P4.1a Inference API: `predict_case(features, measured_mask) -> DecisionRecord`
- [ ] P4.1b Select six guided features by train-only importance and log ADR
- [ ] P4.1c Fit partial-feature imputer on train only and log ADR
- [ ] P4.1d Input validation, range/geometry warnings
- [ ] P4.1e Held-out example-case selection and claim tests
- [x] P4.1f Example-first landing page
- [>] P4.1g Guided six-feature entry
- [ ] P4.1h CSV upload/paste batch triage
- [ ] P4.1i What-if controls and labeled synthetic stress recipe
- [ ] P4.1j Exploratory review-capacity thresholds
- [ ] P4.1k Why-abstain page sourced from results
- [ ] P4.1l Accessible copy, glossary, safety language
- [ ] P4.1m UI smoke and privacy tests
- [ ] P4.1n README screenshots and 90-second viva script






