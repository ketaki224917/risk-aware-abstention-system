# Blockers and author decisions

## Open author review

- [OPEN 2026-10-26] CLAIM-001 - Paper result wording. The source-aligned run reports 13/2,408 accepted errors (0.54%) and 0.912 +/- 0.020 Isolation Forest stress AUROC, versus the journal paper's 17/2,419 (0.70%) and 0.911 +/- 0.019. It also differs on the main-split Assisted/Human counts and combined-risk shift behavior. The implementation records the differences without tuning.
  - Needed from the author: confirm whether to retain the journal values as the originally published experiment and label the source-aligned run separately as an independent reproduction.
  - Recommended wording: report the published values as the original experiment and the source-aligned values as an independent reproduction. See docs/state/RECONCILIATION.md.

- [OPEN 2026-10-29] DATA-001 - A compatible labeled dataset for symptom/history-only predictions remains unavailable.
  - The app now uses the public UCI Mammographic Mass data for age and mammogram report findings (shape, margin, density). Symptoms and family history are context only; without a report the app returns Human Review with no class estimate.
  - The UCI model's held-out malignant sensitivity is 61.8% and its Automatic-tier error rate is 20.0%. It is not suitable for health decisions.
  - The BrEaST candidate was audited: 256 ultrasound-selected adult women, but only 132 of 252 benign/malignant rows have age, physician-observed signs, and symptoms all available; its symptom field is aggregated, not the app's four separate questions. It is not connected.
  - Needed to make symptom answers affect class prediction: a sufficiently sized dataset with matched user-reported inputs and verified benign/malignant outcomes, plus independent validation. Do not generate synthetic labels or present symptoms as supported model inputs.

## Resolved environment issue

- [RESOLVED 2026-10-27] MAKE-001 - GNU Make 4.4.1 is available at D:/msys64/usr/bin/make.exe. make test, make lint, and make app passed in the active D: project. The older C:/MinGW/bin/mingw32-make.exe 3.82.90 still fails before parsing targets with INTERNAL: readdir: Invalid argument, but it is no longer the selected make executable.
- [RESOLVED 2026-10-27] STREAMLIT-001 - A first-run Streamlit activation prompt for email failed under noninteractive Make. The app target now starts headless and disables browser usage statistics; make app starts the server without an email prompt.

## Resolved source questions

- The journal PDF supplied on 2026-10-25 specifies the consequence values, 50-tree bootstrap member size, Isolation Forest scaling, stress-test recipe, main seed, split seed range, and checker fault categories. ADR-009 supersedes the assumptions that were needed before the paper was supplied.
- The original source repository and raw experiment archive have not been provided. The project is a source-aligned independent implementation, not a claim of bit-identical reproduction of the authors' original code.
- Five separately supplied papers are catalogued as background literature in SOURCE_MAP.md; they are not treated as evidence for this project's numerical results.
