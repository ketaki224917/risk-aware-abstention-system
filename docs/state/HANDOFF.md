# HANDOFF

Updated: 2026-10-27 | Session #: 7 | Current phase: P4.1q dataset feasibility / P4.6-P4.7 final acceptance | Status: four-question UI exists, but compatible clinical prediction is blocked by candidate dataset evidence.

## Do next

1. Obtain an approved, de-identified dataset with compatible questionnaire fields and enough confirmed positive outcomes for independent validation; keep the intake at Human Review until then.
2. In a clean clone, run `make setup`, `make test`, `make reproduce`, and `make app`; record current outputs in `docs/state/ENVIRONMENT.md`.
3. Resolve CLAIM-001 paper wording with the author and update P4.6/P4.7.

## Current demo

- Active repository: `D:/ERA CP`.
- The landing page collects age, symptoms, family history, and prior breast history. It returns Human Review with no predicted class because the WDBC classifier is incompatible and the only public questionnaire-like candidate tested failed held-out feasibility.
- Optional WDBC research modes remain available and load the saved WDBC bundle; they do not accept the four questionnaire answers.
- The public Duke BRCA file is retained under `data/` with field scope and provenance documented. It has 987 records, 37 cancer outcomes, and a follow-up outcome after 2002 screening. It is not current diagnosis or benign/malignant pathology data.
- `scripts/audit_questionnaire_dataset.py` reproduces the seed-42 RAA feasibility check. Metrics are recorded in `results/clinical_candidate_audit/metrics.json`; the file is not used by app inference.
- Candidate held-out result: 0/7 cancer outcomes detected; ROC-AUC 0.486537. Do not connect this model to user answers or claim that it detects cancer.
- App health was previously HTTP 200 at `http://localhost:8501`; no app change was made in this audit task.

## Verification

- Candidate audit: 987 rows; split 591/198/198; 37 positive outcomes; test sensitivity 0/7; specificity 168/191; ROC-AUC 0.486537.
- Prior project checks in Session 6: `make test` -> 35 passed; `make lint` -> all checks passed; app health -> HTTP 200, `ok`.
- Re-run `make test`, `make lint`, and `make app` after pulling the current audit files. Fresh-clone setup/reproduction remain unverified.
- CLAIM-001 remains open.

## Worktree / blocker

P4.1q remains blocked under DATA-001: the candidate dataset is unsuitable for an interactive cancer classifier. No changes were made to questionnaire inference or the running app. The D: worktree already contained modifications from prior P4.1 tasks; preserve those while committing the dataset audit.
