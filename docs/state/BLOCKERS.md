# Blockers and author decisions

## Environment constraint

- GNU Make is unavailable in this PowerShell environment. Equivalent `uv` commands were run, but the literal `make setup`, `make test`, `make reproduce`, and `make app` entry points remain unverified here. This is the only outstanding mechanical acceptance check (P4.6).

## Author review

- [OPEN 2026-10-26] CLAIM-001 — paper result wording. The source-aligned run reports 13/2,408 accepted errors (0.54%) and 0.912 ± 0.020 Isolation Forest stress AUROC, versus the journal paper's 17/2,419 (0.70%) and 0.911 ± 0.019. It also differs on the main-split Assisted/Human counts and combined-risk shift behavior. The implementation records the differences without tuning. Author decision: retain the published values as results from the original experiment, or revise/qualify the paper to include the independently reproduced values and implementation details. See `docs/state/RECONCILIATION.md`.

## Resolved source questions

- The journal PDF supplied on 2026-10-25 specifies the consequence values, 50-tree bootstrap member size, Isolation Forest scaling, stress-test recipe, main seed, split seed range, and checker fault categories. ADR-009 supersedes the assumptions that were needed before the paper was supplied.
- The original source repository and raw experiment archive have not been provided. The project is a source-aligned independent implementation, not a claim of bit-identical reproduction of the authors' original code.
- Five separately supplied papers are catalogued as background literature in `SOURCE_MAP.md`; they are not treated as evidence for this project's numerical results.
