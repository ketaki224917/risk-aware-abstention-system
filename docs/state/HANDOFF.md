# HANDOFF

Updated: 2026-11-14 | Session #: 15 | Current task: P4.1ag model-supported intake | Status: complete. The dark local form now collects only saved-model inputs from a mammogram report.
Last completed task commit: 374d078574ab [P4.1ag] Replace unsupported symptom questions with model inputs.

## Do next (exact)

1. Open `http://localhost:8501` on this computer; if the server is stopped, run `make app` from `D:\ERA CP`.
2. Keep DATA-001 open only for a future symptom/history-driven classifier; connect nothing until a suitable matched, verified dataset is obtained and independently validated.
3. Continue P4.6 fresh-clone setup/reproduction and P4.7 paper-versus-run author review.

## Environment state

- Active repo and runtime: `D:\ERA CP`; the D:-only embedded Python 3.13.17 and D: package environment were used. No project/test/cache output was written to C:.
- Streamlit listens at `http://localhost:8501` on IPv6 loopback. On this check, home returned HTTP 200 and `/_stcore/health` returned HTTP 200 with body `ok`.
- Regression: 44 tests passed. `ruff check . --no-cache` passed. `ruff format --check .` reported 77 files already formatted.
- Saved model artifacts remain under `results/mammographic_mass/`; app does not retrain on page load.

## Prediction and report state

- The user-facing form asks whether a mammogram report describes a mass; if yes, it takes scan age, mass shape, edge/margin, and density from the report. Every field enters the saved classifier and RAA pipeline.
- Symptom, family-history, height, weight, and gender questions were removed because the available model/dataset cannot use them. Do not guess report findings.
- No compatible report returns Human Review with no class estimate. Any unknown report finding may be imputed from TRAIN only to run the pipeline, and still forces Human Review.
- Saved-artifact examples reach all routes: age 46, round, clear/smooth edge, low density -> benign/Automatic; age 55, irregular, partly hidden edge, low density -> malignant/Assisted; age 65, lobulated, partly hidden edge, low density -> malignant/Human Review. These are benchmark model outputs, not diagnoses.
- The optional Word report is generated only on request and remains in memory until download. No answers are stored by default.

## WIP / uncommitted

- None.

## Failing tests / issues

- None for P4.1ag. DATA-001 remains open only for any future model driven by self-reported symptoms/history; current report-based model is functional but not suitable for health decisions.

## Gotchas learned

- The four actual classifier inputs are age at scan plus the mammogram report's shape, edge/margin, and density categories. Read these from an existing report; do not infer them from symptoms.
- The saved model estimates a historical mammographic-mass label. It does not diagnose a person. Missing report information is routed to Human Review.
- The BrEaST candidate has only 132 complete binary rows with age, signs, and aggregated symptoms; it is not connected to inference.
