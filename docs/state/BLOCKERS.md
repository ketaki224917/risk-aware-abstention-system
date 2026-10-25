# Blockers

Human-only questions requiring an author decision will be recorded here. No such question has yet been established.

## Environment constraints (work around where possible)
- Python is not installed in the current environment; `py` reports no installed interpreters.
- GNU Make is unavailable in PowerShell.
- There is no original source, paper file, or results archive to inspect.

These are recorded as environment limitations, not human-only questions. Do not mark a scientific claim as blocked until an actual reproduced result demonstrates a conflict that requires author wording.

## Open author decisions
- [OPEN 2026-10-25] CLAIM-001 Paper wording — needed from human: decide whether to revise or qualify the ≈0.70% full-policy accepted-error and ≈0.91 synthetic anomaly-AUROC claims in light of run `raa-20261025-01`; reproduced full-policy pooled error is 1.493%, and the pooled AUROC over the documented 12-variant stress grid is 0.731 (the 10-feature/2σ variant is 0.921). Workaround meanwhile: report all reproduced values and explicitly mark the paper targets unsupported or recipe-dependent.
- [OPEN 2026-10-25] SOURCE-001 Original paper/method details — needed from human: provide the paper or original source repository so consequence values, bootstrap member size, exact synthetic-shift recipe, and explanation-checker figure can be traced. Workaround meanwhile: retain ADR-003 assumptions and avoid claiming exact method-level replication.
