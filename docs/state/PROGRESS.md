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
