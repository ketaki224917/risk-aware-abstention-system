# Environment

## Source-aligned reproduction environment

- Client date: 2026-10-26 (Asia/Calcutta)
- OS shell: Windows PowerShell; platform recorded as Windows 11 build 26200.
- Git: 2.55.0.windows.2
- Runtime: workspace-local embeddable CPython 3.13.17 under `.tools/python-embed/`.
- Dependency manager: uv 0.13.5 at `.tools/python-embed/Scripts/uv.exe`.
- Lock: `uv.lock`; synchronized with `uv sync --all-groups`.
- Key packages: NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, Matplotlib 3.11.2, Streamlit 1.66.1, PyYAML 6.0.3, pytest 8.4.2, Ruff 0.17.2.
- GNU Make: unavailable in PowerShell. The Makefile commands have not been invoked literally; equivalent uv commands passed.
- Hardware details: not recorded.

## Verified commands and evidence

- `uv run python -m pytest -q` -> 12 passed.
- `uv run ruff check .` -> all checks passed.
- `uv run ruff format --check .` -> 53 files already formatted.
- `uv lock --check` -> locked environment resolves; no dependency changes were made.
- `uv run python -m raa.cli reproduce --run-id raa-20261026-paper-aligned-01` -> 30 splits, 3,420 cases, stress, explanation evaluation, and figures generated.
- The seed-42 main split matches the paper's 6 baseline errors (3 FN, 3 FP), 76 automatic cases, zero automatic errors, and 3/3 FN routed away.
- The stress AUROC mean is 0.912 ± 0.020 for Isolation Forest and 0.803 ± 0.035 for uncertainty.
- `uv run streamlit run src/raa/app/streamlit_app.py --server.headless true --server.port 8766` -> `GET /_stcore/health` returned HTTP 200 and `ok`.

The exact local uv executable may require `--cache-dir .tools/uv-cache` in this sandbox because the default user cache is not writable.

## Fresh environment prerequisites

- Python 3.11 or newer
- GNU Make (for Makefile entry points)
- uv 0.13.5
- `make setup` syncs locked dependencies from `uv.lock`.
