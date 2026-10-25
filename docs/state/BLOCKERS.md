# Blockers

Human-only questions requiring an author decision are listed below.

## Environment constraints (work around where possible)
- No system Python is on PATH; a workspace-local CPython 3.13.17 runtime was unpacked under `.tools/` for this run.
- GNU Make is unavailable in PowerShell.
- There is no original source, paper file, or results archive to inspect.

The equivalent uv test/lint/reproduction/app commands were run directly. P4.6 remains open because the literal GNU Make targets were not invoked.

## Open author decisions
- [OPEN 2026-10-25] CLAIM-001 Paper wording — needed from human: decide whether to revise or qualify the ≈0.70% full-policy accepted-error and ≈0.91 synthetic anomaly-AUROC claims in light of run `raa-20261025-01`; reproduced full-policy pooled error is 1.493%, and the pooled AUROC over the documented 12-variant stress grid is 0.731 (the 10-feature/2σ variant is 0.921). Workaround meanwhile: report all reproduced values and explicitly mark the paper targets unsupported or recipe-dependent.
- [OPEN 2026-10-25] SOURCE-001 Original paper/method details — needed from human: provide the paper or original source repository so consequence values, bootstrap member size, exact synthetic-shift recipe, and explanation-checker figure can be traced. Workaround meanwhile: retain ADR-003 assumptions and avoid claiming exact method-level replication.
