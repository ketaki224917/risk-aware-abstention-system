# Environment

## Active D: project environment

- Client date: 2026-10-27 (Asia/Calcutta).
- OS shell: Windows PowerShell; host reported Windows 11 build 26200.
- Active project root: `D:\ERA CP`.
- Runtime used by the new D: environment: CPython 3.13.17; uv 0.13.5.
- Locked dependency environment: `.venv`, synchronized from `uv.lock` with `uv --system-certs --cache-dir .tools/uv-cache sync --all-groups --locked`.
- Key packages: NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, Matplotlib 3.11.2, Streamlit 1.66.1, PyYAML 6.0.3, pytest 8.4.2, Ruff 0.17.2.
- GNU Make status: `C:\MinGW\bin\mingw32-make.exe` is version 3.82.90, but `mingw32-make -n test` fails before reading targets with `INTERNAL: readdir: Invalid argument`. Literal Make targets remain unverified.
- The old C: folder remains as a backup because Windows ACLs denied deleting `.git\hooks` during the cross-volume move. D: contains the complete Git working tree and is the active repository.

## Verified commands and evidence on D:

- `uv --system-certs --cache-dir .tools/uv-cache sync --all-groups --locked` -> 57 resolved, 54 checked.
- `uv --cache-dir .tools/uv-cache run pytest -q` -> 12 passed.
- `uv --cache-dir .tools/uv-cache run ruff check .` -> all checks passed.
- `uv --cache-dir .tools/uv-cache lock --check --offline` -> 57 packages resolved.
- `uv run streamlit run src/raa/app/streamlit_app.py --server.headless true --server.port 8767` -> `GET /_stcore/health` returned HTTP 200 and `ok`.
- Git worktree was clean after the D: checks.

## Canonical experiment

- Run `raa-20261026-paper-aligned-01` was generated before relocation: 30 stratified splits, 3,420 pooled cases, full experiment artifacts under `results/runs/raa-20261026-paper-aligned-01/`.
- A redundant reproduction rerun was interrupted when the user redirected work to move the project. The touched split JSON files were restored from the committed run before the D: worktree was restored. The canonical run remains the logged evidence.

## Fresh setup prerequisites

- Python 3.11 or newer, uv 0.13.5, and network access to fetch missing locked packages on a clean machine.
- A compatible GNU Make is required for literal Makefile targets; direct uv commands are documented in the README.