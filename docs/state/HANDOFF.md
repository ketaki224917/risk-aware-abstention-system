# HANDOFF

Updated: 2026-10-27 | Session #: 4 | Current task: P4.1i what-if exploration | Status: Modes A-C complete; replacement demo in progress.

## Do next

1. Implement the signed 3σ, eight-feature synthetic perturbation helper using TRAIN standard deviations and nonnegative clipping.
2. Add a what-if page with four live sliders on a held-out row and a labeled synthetic-shift button.
3. Test deterministic shift recipe and AppTest live updates; then add capacity mapping and Why abstain detail tests.

## Current state

- Active repository: D:\ERA CP; latest task commit is [P4.1h] Add CSV batch triage.
- P4.1a-h complete. Modes A (examples), B (six measured/24 estimated), and C (CSV batch) use the same saved real model pipeline.
- CSV accepts only 30 named feature columns, up to 100 rows, no ID/demographic fields; it stores no uploaded rows, and downloads triage outputs without values.
- Verification: inference tests 5 passed; example tests 2 passed; tests/test_batch.py tests/test_ui.py -> 5 passed; focused Ruff passed.
- Saved artifact under results/demo and canonical aggregate results remain the data sources. App loader never trains.
- What-if, capacity, expanded why-abstain evidence, all-mode smoke/privacy checks and final README remain.
- GNU Make 3.82.90 and CLAIM-001 remain open.

## WIP files

- README.md remains earlier uncommitted WIP.
- src/raa/app/streamlit_app.py now contains working Modes A-C and will be extended.

## Next 3 commands/actions

- Implement deterministic 8-feature signed 3σ stress input and tests.
- Add four-slider live what-if and synthetic label.
- Update P4.1i state/commit; then implement capacity thresholds and evidence page.
