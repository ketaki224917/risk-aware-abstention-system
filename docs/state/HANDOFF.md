# HANDOFF

Updated: 2026-10-25 | Session #: 1
Current phase/task: P4.6/P4.7 — final acceptance | Status: implementation/reproduction complete; acceptance pending
Last commit: `de348a4` — [P0.3] Track package initializers and results marker

## Do next (exact)
1. Obtain the original paper/source repository and the author's decision on whether to revise or qualify the unsupported full-policy and recipe-dependent stress-test claims in `docs/state/BLOCKERS.md`.
2. In an environment with GNU Make, install the locked dependencies with `make setup`, then run `make test`, `make reproduce`, and `make app`; record the results.
3. Update reconciliation and final acceptance status from the source details and clean-environment checks; do not tune fixed parameters to match targets.

## Environment state
- Workspace initially had no repository or source; user prompt saved verbatim as `AGENTS.md`.
- Git initialized. Initial state commit exists; most implementation and results are currently uncommitted.
- Workspace-local Python 3.13.17 embeddable runtime and uv 0.13.5 are under ignored `.tools/`; `uv.lock` pins the project dependency graph.
- `uv sync --all-groups` completed; 54 packages installed in `.venv`.
- GNU Make is unavailable in PowerShell. Direct uv equivalents were run instead.
- Run `raa-20261025-01` generated 30 splits and 3,420 test cases. Output: `results/runs/raa-20261025-01/`.
- Streamlit server started at port 8765; `/_stcore/health` returned HTTP 200 and `ok`.

## WIP / uncommitted
- None. Project source, tests, docs, state files, and generated run artifacts are committed.
- `.tools/` and `.venv/` are ignored local runtime/setup files.
- Local generated/runtime files under `.tools/` and `.venv/` are ignored.

## Failing tests / issues
- `uv run pytest -q`: 12 passed.
- `uv run ruff check .`: All checks passed.
- `make test` could not start because GNU Make is absent; the equivalent pytest command passed.
- Reproduction does not support the ≈0.70% full-policy error target: pooled error was 1.493%, and uncertainty-only outperformed full policy by 0.783 percentage points on paired split means.
- Pooled AUROC over the 12 documented synthetic shift variants was 0.731; the source paper's exact recipe is unavailable. The 10-feature/2σ variant was 0.921.
- Author decisions SOURCE-001 and CLAIM-001 remain open.

## Gotchas learned
- Python.org installer registration failed with access denied, so a verified embeddable distribution was unpacked locally and pip bootstrapped from a SHA-256-verified official wheel.
- uv needed `--system-certs` for PyPI and a workspace-local `--cache-dir` in this sandbox.
- No original paper, consequence values, bootstrap-member size, stress recipe, or checker figure was available. Those gaps are explicitly logged; do not present assumptions as recovered paper settings.
- The test partition contains 114 cases for each seed; the 30-split pooled count is 3,420.
