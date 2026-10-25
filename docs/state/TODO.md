# Master TODO

Status: `[ ]` todo, `[>]` doing, `[x]` done, `[!]` blocked, `[~]` dropped (with reason). Do not delete task IDs.

## Phase 0 — Foundations
- [x] P0.1 Inspect repo/ZIP; inventory existing files and identify reported-results path (none present; see ADR-001)
- [x] P0.2 Create `docs/state/*`; save the supplied master prompt as root `AGENTS.md`
- [>] P0.3 Create conventions, project metadata, lockfile, Makefile, lint and test setup
- [ ] P0.4 Quarantine unrelated code to `legacy/` with explanation and ADR (no legacy code found)
- [ ] P0.5 Add config module and `config.yaml` for hyperparameters, weights, percentiles, seeds
- [ ] P0.6 Record environment and obtain a passing smoke test

## Phase 1 — Core pipeline
- [ ] P1.1 Dataset loading and stratified 60/20/20 splitting with leakage tests
- [ ] P1.2 RF-300 classifier and baseline metrics
- [ ] P1.3 30-member bootstrap uncertainty and tests
- [ ] P1.4 200-tree Isolation Forest anomaly score and tests
- [ ] P1.5 Consequence module and ADR on values
- [ ] P1.6 Train-fitted normalization and weighted risk engine with tests
- [ ] P1.7 Validation 70th/90th percentile policy with tests
- [ ] P1.8 Single-case inference API and structured decision record

## Phase 2 — Explanations
- [ ] P2.1 Decision record schema
- [ ] P2.2 Deterministic template explanation generator
- [ ] P2.3 Rule-based explanation checker
- [ ] P2.4 Fault injection and per-type detection evaluation
- [ ] P2.5 Read-only explanation guarantee and test
- [ ] P2.6 Optional exploratory LLM adapter (only if useful; never claim unevaluated results)

## Phase 3 — Experiments
- [ ] P3.1 Resumable 30-split pooled evaluation (3,420 test cases)
- [ ] P3.2 Main results and paper reconciliation
- [ ] P3.3 Paired ablations
- [ ] P3.4 Risk-coverage and percentile sweep
- [ ] P3.5 Uncertainty diagnostics, reliability, and ECE
- [ ] P3.6 Synthetic anomaly stress test and policy behavior under shift
- [ ] P3.7 Explanation checker evaluation
- [ ] P3.8 Sensitivity analyses
- [ ] P3.9 Optional non-demographic proxy subgroup analysis
- [ ] P3.10 End-to-end `make reproduce`

## Phase 4 — App and documentation
- [ ] P4.1 Demo app with three levels and clinical-use disclaimer
- [ ] P4.2 Visualizations
- [ ] P4.3 README with architecture, quickstart, real results, limitations, reported-results path
- [ ] P4.4 Method, limitations, and results documentation
- [ ] P4.5 Viva guide with walkthrough, questions, and claim boundaries
- [ ] P4.6 Fresh-environment setup, reproduction, and app checks
- [ ] P4.7 Final acceptance verification
