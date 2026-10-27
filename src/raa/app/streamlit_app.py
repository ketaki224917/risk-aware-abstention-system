"""Example-first Streamlit interface for the local RAA research prototype."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import streamlit as st

from raa.app.copy import BANNER, GLOSSARY, INPUT_HELP, LIMITS, PRIVACY
from raa.app.demo_assets import DemoArtifact, load_demo_artifact, load_paper_results
from raa.app.examples import ExampleCase, select_example_cases
from raa.data import BreastCancerData, DataSplit, load_breast_cancer_data, stratified_split
from raa.explain.checker import check_explanation
from raa.explain.record import DecisionRecord
from raa.explain.templates import generate_explanation
from raa.inference import CaseInputError, predict_case
from raa.risk.policy import DecisionLevel


@dataclass(frozen=True)
class DemoState:
    data: BreastCancerData
    split: DataSplit
    artifact: DemoArtifact
    examples: dict[str, ExampleCase]
    test_records: tuple[DecisionRecord, ...]


@st.cache_resource(show_spinner="Loading the saved research modelÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦")
def load_demo_state() -> DemoState:
    """Load saved models and score held-out test examples without fitting anything."""
    artifact = load_demo_artifact()
    data = load_breast_cancer_data()
    split = stratified_split(data.targets, seed=artifact.run_seed)
    test_records = artifact.system.predict(data.features[split.test])
    examples = select_example_cases(data, split, test_records)
    return DemoState(data, split, artifact, examples, test_records)


def render_result(record: DecisionRecord, *, synthetic: bool = False) -> None:
    """Display a human-readable route, component scores, and checked explanation."""
    label = record.predicted_label
    if record.level is DecisionLevel.AUTOMATIC:
        st.success(f"\U0001f7e2 Automatic ? the model leans {label}.")
        st.write(
            "The research policy returned this case in its Automatic tier. This is not a diagnosis."
        )
    elif record.level is DecisionLevel.ASSISTED:
        st.warning(
            f"\U0001f7e1 Assisted ? the model leans {label}; additional verification is advised."
        )
    else:
        st.error(
            f"\U0001f534 Human Review ? the model leans {label}; a human should review this case."
        )
    st.caption("The class is a model estimate. The route describes this prototype's policy.")
    if synthetic:
        st.info(
            "Synthetic what-if profile: generated using the paper's signed 3-sigma shift recipe."
        )

    if record.measured_feature_count == 30:
        st.caption("30 of 30 features measured; 0 estimated.")
    else:
        st.caption(
            f"{record.measured_feature_count} of 30 measured, "
            f"{record.estimated_feature_count} estimated."
        )
    for warning in record.input_warnings:
        st.warning(warning)

    st.subheader("Signals used by the route")
    columns = st.columns(3)
    for column, title, value, help_text in zip(
        columns,
        ("Model disagreement", "Unusualness", "Cost of error"),
        (record.uncertainty, record.anomaly, record.consequence),
        (
            GLOSSARY["Model disagreement"],
            GLOSSARY["Unusualness"],
            GLOSSARY["Cost of error"],
        ),
        strict=True,
    ):
        with column:
            st.progress(int(np.clip(value, 0, 1) * 100), text=f"{title}: {value:.2f}")
            st.caption(help_text)

    st.subheader("Combined risk")
    st.progress(int(np.clip(record.risk, 0, 1) * 100), text=f"Risk score: {record.risk:.3f}")
    st.caption(
        f"Automatic through {record.automatic_threshold:.3f} Ãƒâ€šÃ‚Â· "
        f"Assisted through {record.assisted_threshold:.3f} Ãƒâ€šÃ‚Â· "
        f"Human Review above {record.assisted_threshold:.3f}."
    )
    st.markdown(
        f"<div role='img' aria-label='Risk gauge: {record.risk:.3f}. "
        f"Automatic threshold {record.automatic_threshold:.3f}; "
        f"Human Review starts above {record.assisted_threshold:.3f}.' "
        "style='position:relative;height:8px;background:#d9dee7;border-radius:5px'>"
        f"<div style='width:{np.clip(record.risk, 0, 1) * 100:.2f}%;height:8px;"
        "background:#315b8a;border-radius:5px'></div></div>",
        unsafe_allow_html=True,
    )

    explanation = generate_explanation(record)
    check = check_explanation(record, explanation)
    with st.expander("Grounded explanation and checker"):
        st.write(explanation)
        if check.passed:
            st.success("ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦ Rule-based checker passed.")
        else:
            st.error("Checker issues: " + ", ".join(check.issues))

    with st.popover("Glossary"):
        for term, definition in GLOSSARY.items():
            st.markdown(f"**{term}** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â {definition}")
    with st.expander("How computed"):
        st.latex(r"R = 0.5U + 0.2A + 0.3C")
        st.write(
            "U is bootstrap-model disagreement, A is normalized Isolation Forest unusualness, "
            "and C is the assumed consequence value. "
            "Validation percentiles set the routing thresholds."
        )
        st.warning(LIMITS)


def render_examples(state: DemoState) -> None:
    st.header("Start with an example case")
    st.write("Choose a one-click case from the held-out test split. No typing is needed.")
    st.caption(INPUT_HELP)
    selected_key = st.session_state.get("selected_example")
    keys = tuple(state.examples)
    for start in range(0, len(keys), 3):
        columns = st.columns(3)
        for column, key in zip(columns, keys[start : start + 3], strict=False):
            case = state.examples[key]
            with column, st.container(border=True):
                st.markdown(f"**{case.title}**")
                st.caption(case.description)
                if st.button("Open example", key=f"open_{case.key}", use_container_width=True):
                    st.session_state["selected_example"] = case.key
                    selected_key = case.key
    if selected_key in state.examples:
        case = state.examples[selected_key]
        row = state.data.features[case.dataset_row]
        record = predict_case(
            row,
            np.ones(row.size, dtype=bool),
            context=state.artifact.inference_context,
        )
        st.divider()
        st.subheader(case.title)
        reveal = st.checkbox("Reveal the recorded dataset label", key=f"reveal_{case.key}")
        if reveal:
            target = int(state.data.targets[case.dataset_row])
            st.info(f"Recorded WDBC dataset label: {'malignant' if target == 0 else 'benign'}.")
        render_result(record)


def _sync_number_from_slider(slider_key: str, number_key: str) -> None:
    st.session_state[number_key] = st.session_state[slider_key]


def _sync_slider_from_number(slider_key: str, number_key: str, lower: float, upper: float) -> None:
    value = st.session_state[number_key]
    if value is not None:
        st.session_state[slider_key] = float(np.clip(value, lower, upper))


def render_guided_entry(state: DemoState) -> None:
    st.header("Guided entry: six measured values")
    st.write(INPUT_HELP)
    st.caption(PRIVACY)
    st.info(
        "Enter six mean measurements from a compatible WDBC record. "
        "The remaining 24 are estimated by a KNN imputer fitted on TRAIN only."
    )
    st.markdown("**6 of 30 measured, 24 estimated**")
    train = state.data.features[state.split.train]
    values: dict[str, float] = {}
    with st.container(border=True):
        for feature in state.artifact.guided_features:
            index = state.data.feature_names.index(feature)
            p05, p95 = np.quantile(train[:, index], [0.05, 0.95])
            low, high = float(train[:, index].min()), float(train[:, index].max())
            default = float(np.median(train[:, index]))
            step = max((high - low) / 500.0, 0.001)
            slider_key = f"guided_slider_{index}"
            number_key = f"guided_number_{index}"
            st.markdown(f"**{feature.title()}**")
            help_text = (
                f"Typical TRAIN range (5thâ€“95th percentile): {p05:.3g}â€“{p95:.3g}. "
                "Values outside the observed TRAIN range are accepted with a warning."
            )
            slider_col, number_col = st.columns([2, 1])
            if slider_key not in st.session_state:
                st.session_state[slider_key] = default
            if number_key not in st.session_state:
                st.session_state[number_key] = default
            with slider_col:
                st.slider(
                    f"{feature.title()} slider",
                    min_value=low,
                    max_value=high,
                    step=step,
                    help=help_text,
                    key=slider_key,
                    on_change=_sync_number_from_slider,
                    args=(slider_key, number_key),
                )
            with number_col:
                st.number_input(
                    f"{feature.title()} exact value",
                    step=step,
                    help=help_text,
                    key=number_key,
                    on_change=_sync_slider_from_number,
                    args=(slider_key, number_key, low, high),
                )
            values[feature] = float(st.session_state[number_key])
    if st.button("Assess these six measurements", type="primary"):
        row = np.full(len(state.data.feature_names), np.nan, dtype=np.float64)
        measured = np.zeros(row.size, dtype=bool)
        for feature, value in values.items():
            index = state.data.feature_names.index(feature)
            row[index] = value
            measured[index] = True
        try:
            record = predict_case(row, measured, context=state.artifact.inference_context)
        except CaseInputError as error:
            st.error(str(error))
        else:
            render_result(record)


def render_why_abstain() -> None:
    results = load_paper_results()
    pooled = results["pooled_case_metrics"]
    levels = results["pooled_decision_level_metrics"]
    st.header("Why does the system abstain?")
    st.write(
        "The policy routes uncertain, unusual, or higher-consequence cases for additional review. "
        "These aggregate values are loaded from the canonical 30-split results file."
    )
    st.caption(f"Run ID: {results['run_id']} Ãƒâ€šÃ‚Â· {results['test_cases']:,} held-out records")
    cols = st.columns(4)
    cols[0].metric("Baseline error rate", f"{pooled['error_rate']:.2%}")
    cols[1].metric("Automatic coverage", f"{pooled['automatic_coverage']:.2%}")
    cols[2].metric("Automatic selective error", f"{levels['Automatic']['error_rate']:.2%}")
    cols[3].metric(
        "Baseline false negatives routed away",
        f"{pooled['false_negatives_routed_away']}/{pooled['false_negatives']} "
        f"({pooled['false_negatives_routed_away_rate']:.1%})",
    )
    st.subheader("How the workload split looked in the recorded run")
    for level in ("Automatic", "Assisted", "Human Review"):
        metric = levels[level]
        st.write(
            f"**{level}:** {metric['count']:,} cases ({metric['share']:.1%}); "
            f"{metric['errors']:,} classifier errors in that tier."
        )
    st.warning(
        "These are research-run summaries, not guarantees for new inputs. Disagreement is not "
        "calibrated error probability; anomaly evaluation uses synthetic shifts only."
    )


def main() -> None:
    st.set_page_config(
        page_title="Risk-Aware Abstention", page_icon="ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â­", layout="wide"
    )
    st.title("Risk-Aware Abstention")
    st.error("ÃƒÂ¢Ã…Â¡Ã‚Â ÃƒÂ¯Ã‚Â¸Ã‚Â " + BANNER)
    st.caption(PRIVACY)
    st.sidebar.caption("Local research demo Ãƒâ€šÃ‚Â· no names or demographic fields")
    mode = st.sidebar.radio(
        "Choose a mode",
        ("Example cases", "Guided entry", "Upload CSV", "What-if", "Why abstain?"),
    )
    try:
        state = load_demo_state()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()
    if mode == "Example cases":
        render_examples(state)
    elif mode == "Guided entry":
        render_guided_entry(state)
    elif mode == "Why abstain?":
        render_why_abstain()
    else:
        st.info("This mode is being prepared; choose Example cases for the working one-click demo.")


if __name__ == "__main__":
    main()
