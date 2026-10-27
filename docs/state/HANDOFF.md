# HANDOFF

Updated: 2026-10-27 | Session #: 8 | Current phase: P4.1q dataset feasibility / P4.6-P4.7 final acceptance | Status: polished four-question intake is available, but model predictions from those answers are blocked by dataset compatibility and validation evidence.

## Do next

1. Obtain an approved, de-identified dataset with the four compatible questionnaire inputs and confirmed benign/malignant pathology labels, with enough cases for independent validation. Keep the intake at Human Review until then.
2. In a clean clone, run make setup, make test, make reproduce, and make app; record outputs in docs/state/ENVIRONMENT.md.
3. Resolve CLAIM-001 paper wording with the author and update P4.6/P4.7.

## Current demo

- Active repository: D:/ERA CP.
- The landing page collects age, symptoms, family history, and prior breast history. It returns Human Review - no prediction made because the WDBC classifier cannot use these answers and the only public questionnaire-like candidate tested failed feasibility.
- The page uses a light, responsive visual theme and keeps the research prototype/non-diagnosis notice visible.
- Optional WDBC research modes remain available and load saved artifacts; they do not accept the four questionnaire answers.
- The Duke BRCA source is retained under data/ with provenance and limitations. It has 987 screening records, 37 follow-up cancer outcomes, and does not provide confirmed current benign/malignant pathology labels.
- Reproduce the candidate audit with python scripts/audit_questionnaire_dataset.py; metrics are in results/clinical_candidate_audit/metrics.json.
- Held-out result: sensitivity 0/7; specificity 168/191 (87.96%); ROC-AUC 0.486537. Do not connect this candidate to the intake or expose its class predictions.

## Verification

- Dataset feasibility audit reproduced before Session 8; full project make test (37 passed) and make lint (all checks passed) passed before the final CSS-only styling change.
- The CSS change was reviewed in source; no tests or browser smoke check were run after it.
- Previous app health check returned HTTP 200 at http://localhost:8501; check after restart/hot reload if reviewing the updated theme.
- Fresh-clone setup/reproduction and CLAIM-001 author wording remain open.
