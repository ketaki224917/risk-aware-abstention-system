# HANDOFF

Updated: 2026-11-14 | Session #: 14 | Current task: P4.1af route troubleshooting | Status: complete; full report inputs return a model result, and Human Review is expected when the report is missing or incomplete.
Last commit before this HANDOFF update: dd81e98 [P4.1ad] Audit questionnaire dataset fit.

## Do next

1. Ask for a sufficiently sized, de-identified dataset with the same self-reported inputs and verified benign/malignant outcomes, or use the current app with actual mammogram report fields.
2. If suitable data arrives, audit missingness and leakage, then evaluate with a patient-level independent test before connecting it to the UI. Never use synthetic labels as real predictions.
3. Continue P4.6 fresh-clone setup/reproduction and P4.7 paper-versus-run author review when DATA-001 is resolved.

## Environment

- Active repo: D:/ERA CP; project and candidate data are on D:.
- The active Streamlit app remains at http://localhost:8501, bound to IPv6 loopback.
- D:-only embedded Python 3.13.17 was used for the candidate audit, prediction, DOCX, and Streamlit AppTest smoke checks. Its caches, temporary files, and logs are on D:.
- The project .venv points at a Python installation on C:, so it was not used.

## Prediction and report state

- User-facing classifier is still the saved real UCI Mammographic Mass model. Age plus report shape, margin, and density change the class lean and RAA score; symptoms, family history, height, weight, and gender are report context only.
- Without a mammogram report, or with a report field marked Not sure, the app routes to Human Review. A complete compatible report input was exercised in Streamlit AppTest and returned Automatic with a benign model lean and no app exceptions.
- BrEaST metadata is saved under data/ and audited under results/br_east_candidate_audit/; it is not connected to inference. It has only 132/252 benign/malignant rows with age, signs, and symptoms present; its signs and aggregated symptom field do not match the requested self-reported form.
- Word DOCX generation remains in memory after the user requests a report. A direct smoke check verified distinct benign/malignant outputs for two mammogram profiles and a valid 4,296-byte Word package.

## WIP / uncommitted

- None.

## Failing tests / issues

- Focused pytest could not run because pytest is not installed in the D:-only embedded runtime. The existing project virtual environment references Python on C:.
- No user-facing code was changed in this troubleshooting task; no synthetic labels or predictions were added.

## Gotchas learned

- To see a class lean in the current app, answer Yes to having a mammogram report and enter age, shape, margin, and density from it. Not sure on a report field triggers Human Review.
- The BrEaST source uses a physician-observed Signs field and an aggregated Symptoms field; these are not the app's four independent self-reported symptom questions.
- The candidate audit can be reproduced with python scripts/audit_breast_symptom_candidate.py.
