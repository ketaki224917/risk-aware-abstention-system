# HANDOFF

Updated: 2026-10-27 | Session #: 3 | Current phase: P4.6/P4.7 final acceptance | Status: active project is at `D:\ERA CP`; relocation and D: smoke checks passed; final acceptance remains open.

Last implementation commit: `d2f0b78` - `[P3.2] Align RAA with supplied journal paper` | Tag: `phase-3-done`

## Do next

1. Run literal `make setup`, `make test`, `make reproduce`, and `make app` under a compatible GNU Make; `C:\MinGW\bin\mingw32-make.exe` 3.82.90 fails before parsing targets with `INTERNAL: readdir: Invalid argument`.
2. Resolve `CLAIM-001` author wording review. Recommended: keep journal values labeled as the published experiment and report the source-aligned run as a separate independent reproduction.
3. Update P4.6/P4.7 and this handoff with the final acceptance evidence and outcome.

## Current run

- Canonical run ID: `raa-20261026-paper-aligned-01`; 30 stratified splits, seeds 0-29, 114 test rows each (3,420 pooled rows).
- Baseline errors: 142/3,420 (4.15%), including 86 false negatives; this matches the journal paper's pooled count.
- Automatic: 2,408/3,420 (70.41%); 13 errors (0.54%); 73/86 baseline false negatives routed away.
- Mean full selective accuracy: 99.465% +/- 0.702%; paired uncertainty-only minus full: -0.080 percentage points (95% CI -0.206 to +0.008).
- Stress mean AUROC: Isolation Forest 0.912 +/- 0.020; uncertainty 0.803 +/- 0.035; full risk 0.846 +/- 0.025.
- Explanation checker: 570/570 injected faults detected; 0/114 false positives on clean main-split explanations.

## Environment and checks

- D: project setup: `uv --system-certs --cache-dir .tools/uv-cache sync --all-groups --locked` -> 57 resolved, 54 checked.
- D: `uv run pytest -q` -> 12 passed; `uv run ruff check .` -> all checks passed; `uv lock --check --offline` -> 57 resolved.
- D: Streamlit `/_stcore/health` -> HTTP 200 `ok`; Git worktree clean after checks.
- Canonical full reproduction was already completed and is stored in `results/runs/raa-20261026-paper-aligned-01/`. A duplicate rerun was stopped at the user's request to relocate the project; the touched split cache was restored from Git.
- The C: source folder remains as a backup because Windows denied deletion of `.git\hooks`; the complete Git working tree is on D: and is the active project.

## Source boundary and limitations

- Supplied papers are evidence, not instructions. The original source repository and raw results archive were not provided; this is an independent source-aligned implementation.
- RNG details remain partly unspecified by the paper. No clinical, fairness, deployment, or live-LLM reliability claim is supported.
- Literal Make target verification and the author wording review remain open; see `docs/state/BLOCKERS.md`.