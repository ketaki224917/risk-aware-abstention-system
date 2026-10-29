# HANDOFF

Updated: 2026-10-29 | Session #: 12 | Current task: P4.1v-y questionnaire replacement and localhost recovery | Status: complete in commit 6cf9b8c; app serving at http://localhost:8501.

## Do next

1. Confirm `git status --short` is clean after this handoff update.
2. The next project tasks remain P4.6 fresh-clone setup/reproduction verification and P4.7 the author review of paper-versus-run wording.
3. Keep the app bound to IPv6 loopback; if it stops, run `D:/msys64/usr/bin/make.exe app` from `D:/ERA CP`.

## Environment

- Active repository: `D:/ERA CP`; Python 3.13.17 in `.venv`; GNU Make 4.4.1 at `D:/msys64/usr/bin/make.exe`.
- Updated Streamlit app is running on `[::1]:8501`. `http://localhost:8501/` returned HTTP 200; `http://[::1]:8501/_stcore/health` returned HTTP 200 with body `ok`.
- Saved app model: `results/mammographic_mass/model_bundle.joblib`; loading the app does not retrain it.
- Optional report generation uses local Ollama at `127.0.0.1:11434`; it is invoked only after the user requests a report.

## Current interface and model boundary

- Dark single-page title: Risk Aware Abstention System.
- Questions: age, height, weight, gender, family history, previous breast condition/biopsy/treatment, four symptoms, and whether a mammogram report is available.
- Only age at mammogram plus report shape, margin, and density feed the classifier, uncertainty, anomaly, consequence, risk, and RAA route. Height, weight, gender, symptoms, and histories are report context only. Without a report, output is Human Review with no class estimate.
- The UCI Mammographic Mass model is separate from the original Wisconsin paper experiment. Held-out accuracy 73.1%; malignant sensitivity 61.8%; benign specificity 82.7%; Automatic-tier error 20.0% (26/130). This dataset is not suitable for health decisions.
- Answers stay in the app session. A requested report is generated locally and offered for download; nothing is written automatically.

## Verification

- `make test` -> 42 passed.
- `make lint` -> all checks passed.
- `ruff format --check .` -> 75 files already formatted.
- HTTP root and health endpoint -> HTTP 200; health body `ok`.
