# Environment

## Active D: project environment

- Client date: 2026-10-27 (Asia/Calcutta).
- OS shell: Windows PowerShell; host reported Windows 11 build 26200.
- Active project root: D:/ERA CP.
- Runtime used by the D: environment: CPython 3.13.17; uv 0.13.5.
- Locked dependency environment: .venv, synchronized from uv.lock with uv --system-certs --cache-dir .tools/uv-cache sync --all-groups --locked.
- Key packages: NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, Matplotlib 3.11.2, Streamlit 1.66.1, PyYAML 6.0.3, pytest 8.4.2, Ruff 0.17.2.
- Selected GNU Make: D:/msys64/usr/bin/make.exe 4.4.1. The older C:/MinGW/bin/mingw32-make.exe 3.82.90 has a readdir error but is not selected by PATH.
- The old C: folder remains as a backup because Windows ACLs denied deleting .git/hooks during the cross-volume move. D: contains the complete Git working tree and is the active repository.

## Verified commands and evidence on D:

- make test -> 35 passed.
- make lint -> all checks passed.
- uv --cache-dir .tools/uv-cache run ruff format --check . -> 66 files already formatted.
- uv --cache-dir .tools/uv-cache lock --check --offline -> 57 packages resolved.
- make app -> server started at http://localhost:8501; GET /_stcore/health returned HTTP 200 and ok. The recipe sets server.headless=true and browser.gatherUsageStats=false.
- Fresh-clone make setup and make reproduce have not been re-run. The canonical experiment remains available under results/runs/raa-20261026-paper-aligned-01/.

## Canonical experiment

- Run raa-20261026-paper-aligned-01: 30 stratified splits, 3,420 pooled test rows, with artifacts under results/runs/raa-20261026-paper-aligned-01/.
- Reproduced baseline errors match 142/3,420 (86 false negatives). Automatic coverage is 70.41%, accepted errors are 13/2,408 (0.54%), 73/86 baseline false negatives are routed away, and Isolation Forest stress AUROC is 0.912 +/- 0.020.
- The journal result discrepancies and author wording question are recorded in docs/state/RECONCILIATION.md and docs/state/BLOCKERS.md.

## Fresh setup prerequisites

- Python 3.11 or newer, uv 0.13.5, and network access to fetch missing locked packages on a clean machine.
- A fresh clone should run make setup, make test, make reproduce, and make app. The full fresh-clone setup/reproduction sequence remains outstanding.


## Local LLM (2026-10-28)

- Ollama was listening at 127.0.0.1:11434. Its local model list included qwen2.5:1.5b (used by the intake summary) and embeddinggemma:latest.
- The app calls only the local Ollama API at 127.0.0.1:11434/api/chat; it does not send health answers or cell measurements. OLLAMA_MODEL can select a different installed local model.
- A synthetic status-only request to qwen2.5:1.5b returned valid Human Review/no-class-estimate wording. No real user answers were sent.
- Updated app launch: uv run --project "D:/ERA CP" streamlit run src/raa/app/streamlit_app.py --server.headless=true --browser.gatherUsageStats=false --server.address=127.0.0.1.
- Current URL: http://127.0.0.1:8501. Health endpoint returned HTTP 200 with body ok; root page returned HTTP 200.
