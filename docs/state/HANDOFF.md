# HANDOFF

Updated: 2026-10-27 | Session #: 4 | Current task: P4.1f example-first landing page | Status: P4.1a-e complete; replacement demo in progress.

## Do next

1. Replace `src/raa/app/streamlit_app.py` with a Streamlit shell that loads `results/demo/model_bundle.joblib` and lands on six one-click held-out example cards.
2. Render decisions using icon + text, careful “model leans” wording, component bars, risk thresholds, checker status, and permanent prototype banner.
3. Test Mode A and its label reveal toggle; continue with guided entry Mode B and batch Mode C.

## Current state

- Active repository: `D:\ERA CP`; latest task commit is `[P4.1e] Add verified test examples and saved demo bundle`.
- P4.1a-e complete. ADR-010 to ADR-014 define inference API, six fields, train-only KNN imputer, validation warnings, offline artifact, and test-only example selection.
- Saved bundle: `results/demo/model_bundle.joblib` (1,308,233 bytes, seed 42; TRAIN/validation/test = 341/114/114), with manifest, feature importance CSV, and six-case JSON catalog. Guided fields are verified to match the top six mean-feature importances fit on TRAIN only.
- The example tests use actual seed-42 held-out model predictions and verify low risk, high concern, borderline Human Review, top-decile anomaly, baseline error, and deterministic random category. The artifact loader test forces any retraining attempt to fail.
- Focused example tests: 2 passed; inference tests: 5 passed. Full baseline suite was 12 passed before app replacement began.
- `make app` now has a missing-artifact build prerequisite; normal fresh-clone use loads the committed bundle and does not retrain.
- `README.md` and `src/raa/app/streamlit_app.py` remain earlier uncommitted edits; replace the app fully, then refresh docs.
- GNU Make 3.82.90 and paper wording `CLAIM-001` remain open.

## WIP files

- `src/raa/app/streamlit_app.py` is still the old incomplete WIP; it is next to be replaced.
- `README.md` has an earlier user-facing form note to reconcile with final UI.

## Next 3 commands/actions

- Replace the Streamlit app with the example-first landing page and reusable result renderer.
- Add AppTest smoke coverage for examples, banner, and reveal toggle.
- Update P4.1f state and commit; then implement six-field guided entry.
