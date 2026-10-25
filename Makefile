.PHONY: setup test lint reproduce ablate stress explain-eval app all

UV ?= uv

setup:
	$(UV) --cache-dir .tools/uv-cache sync --all-groups --locked

test:
	$(UV) --cache-dir .tools/uv-cache run pytest -q

lint:
	$(UV) --cache-dir .tools/uv-cache run ruff check .

reproduce:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.cli reproduce

ablate:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.cli ablate

stress:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.cli stress

explain-eval:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.cli explain-eval

app:
	$(UV) --cache-dir .tools/uv-cache run streamlit run src/raa/app/streamlit_app.py

all: test lint reproduce
