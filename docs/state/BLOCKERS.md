# Blockers and author decisions

## Environment constraint

- [OPEN 2026-10-27] MAKE-001 - `C:\MinGW\bin\mingw32-make.exe` 3.82.90 is present, but `mingw32-make -n test` fails before parsing targets with `INTERNAL: readdir: Invalid argument`. D: setup, tests, Ruff, lock check, and app health passed via the equivalent uv commands. Needed to close P4.6: run literal `make setup`, `make test`, `make reproduce`, and `make app` with a compatible GNU Make.

## Author review

- [OPEN 2026-10-26] CLAIM-001 - paper result wording. The source-aligned run reports 13/2,408 accepted errors (0.54%) and 0.912 +/- 0.020 Isolation Forest stress AUROC, versus the journal paper's 17/2,419 (0.70%) and 0.911 +/- 0.019. It also differs on the main-split Assisted/Human counts and combined-risk shift behavior. The implementation records the differences without tuning. Recommended wording: retain the journal values as the originally published experiment and label the source-aligned run separately as an independent reproduction. See `docs/state/RECONCILIATION.md`.

## Resolved source questions

- The journal PDF supplied on 2026-10-25 specifies the consequence values, 50-tree bootstrap member size, Isolation Forest scaling, stress-test recipe, main seed, split seed range, and checker fault categories. ADR-009 supersedes the assumptions that were needed before the paper was supplied.
- The original source repository and raw experiment archive have not been provided. The project is a source-aligned independent implementation, not a claim of bit-identical reproduction of the authors' original code.
- Five separately supplied papers are catalogued as background literature in `SOURCE_MAP.md`; they are not treated as evidence for this project's numerical results.