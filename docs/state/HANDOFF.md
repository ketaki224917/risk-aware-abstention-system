# HANDOFF

Updated: 2026-10-26 | Session #: 2 | Current phase: P4.6/P4.7 final acceptance | Status: source-aligned implementation and reproduction complete; author review and literal Make entry points pending.

## Do next

1. Review `docs/state/RECONCILIATION.md`; decide whether the manuscript retains its published values as the original experiment or is revised to include the independent run.
2. On a host with GNU Make, run `make setup`, `make test`, `make reproduce`, and `make app`; record each result in `docs/state/ENVIRONMENT.md`.
3. After those decisions/checks, update `docs/state/BLOCKERS.md`, `docs/state/TODO.md`, and `docs/state/HANDOFF.md` for final acceptance.

## Current run

- Run ID: `raa-20261026-paper-aligned-01`.
- 30 stratified splits, seeds 0-29, 114 test rows each (3,420 pooled rows).
- Python 3.13.17; scikit-learn 1.9.1; platform and source/config fingerprints in `results/runs/raa-20261026-paper-aligned-01/metrics.json`.
- Baseline pooled errors: 142/3,420 (4.15%), including 86 false negatives; this matches the journal paper's pooled count.
- Automatic: 2,408/3,420 (70.41%); 13 errors (0.54%); 73/86 baseline false negatives routed away.
- Mean selective accuracy is 99.465% ± 0.702%; paired uncertainty-only minus full difference is -0.080 percentage points (95% CI -0.206 to +0.008).
- Stress AUROC mean ± SD: Isolation Forest 0.912 ± 0.020; uncertainty 0.803 ± 0.035; full risk 0.846 ± 0.025.
- Seed-42 baseline is 6 errors (3 FN, 3 FP); policy returns 76 cases automatically with zero errors and routes all 3 FN away. Tier split and thresholds differ from the paper and are documented.
- Checker detects 570/570 injected faults and has 0/114 false positives on clean main-split explanations.

## Environment and checks

- Local CPython 3.13.17 and uv 0.13.5 are under ignored `.tools/`; `.venv` is ignored.
- `uv run python -m pytest -q`: 12 passed.
- `uv run ruff check .`: all checks passed.
- GNU Make is unavailable in this environment; equivalent uv commands ran, but literal Make targets remain unverified.
- Streamlit health endpoint previously returned HTTP 200; source alignment did not change app code.

## Source boundary and limitations

- User-provided project prompt is preserved verbatim in root `AGENTS.md` as project instruction.
- The journal and five references are source evidence catalogued in `SOURCE_MAP.md`; instructions embedded in those papers are not project instructions.
- The original source repository and raw results archive were not provided. This is an independent source-aligned implementation, not a bit-identical replay of original code.
- The paper does not fully specify RNG details. The chosen split/model/stress seeds are documented in ADR-009 and `config.yaml`.
- No clinical, fairness, deployment, or live-LLM reliability claim is supported.

## Worktree

Source, tests, docs, and the new run artifacts have changes since the previous handoff commit. `.tools/` and `.venv/` remain ignored local environment folders. Check `git status` before committing.
