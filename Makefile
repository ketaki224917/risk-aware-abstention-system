.PHONY: setup test lint reproduce ablate stress explain-eval demo-artifact mammography-artifact app all

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

demo-artifact:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.app.prepare_demo_artifact

results/demo/model_bundle.joblib:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.app.prepare_demo_artifact

app: results/mammographic_mass/model_bundle.joblib
	$(UV) --cache-dir .tools/uv-cache run streamlit run src/raa/app/streamlit_app.py --server.headless=true --browser.gatherUsageStats=false --server.address=::1

all: test lint reproduce


mammography-artifact:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.app.prepare_mammography_artifact

results/mammographic_mass/model_bundle.joblib:
	$(UV) --cache-dir .tools/uv-cache run python -m raa.app.prepare_mammography_artifact
