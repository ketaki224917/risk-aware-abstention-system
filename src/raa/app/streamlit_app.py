"""Example-first Streamlit interface for the local RAA research prototype."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

import numpy as np
import streamlit as st

from raa.app.copy import BANNER, GLOSSARY, INPUT_HELP, LIMITS, PRIVACY
from raa.app.demo_assets import DemoArtifact, load_demo_artifact, load_paper_results
from raa.app.examples import ExampleCase, select_example_cases
from raa.config import load_config
from raa.data import BreastCancerData, DataSplit, load_breast_cancer_data, stratified_split
from raa.explain.checker import check_explanation
from raa.explain.record import DecisionRecord
from raa.explain.templates import generate_explanation
from raa.inference import (
    CaseInputError,
    csv_template,
    predict_case,
    predict_csv,
    reroute_case_record,
    synthetic_shift_case,
    thresholds_for_review_capacity,
)
from raa.risk.policy import DecisionLevel


@dataclass(frozen=True)
class DemoState:
    data: BreastCancerData
    split: DataSplit
    artifact: DemoArtifact
    examples: dict[str, ExampleCase]
    test_records: tuple[DecisionRecord, ...]


@st.cache_resource(show_spinner="Loading the saved research model...")
def load_demo_state() -> DemoState:
    """Load saved models and score held-out test examples without fitting anything."""
    artifact = load_demo_artifact()
    data = load_breast_cancer_data()
    split = stratified_split(data.targets, seed=artifact.run_seed)
    test_records = artifact.system.predict(data.features[split.test])
    examples = select_example_cases(data, split, test_records)
    return DemoState(data, split, artifact, examples, test_records)


def render_review_capacity(record: DecisionRecord, state: DemoState) -> DecisionRecord:
    """Map an exploratory review workload slider to the saved validation-risk distribution."""
    with st.expander("Review capacity (exploratory)"):
        capacity = st.slider(
            "How many of 100 cases can your team review?",
            min_value=5,
            max_value=60,
            value=30,
            step=1,
            key="review_capacity_per_100",
        )
        thresholds, automatic_p, assisted_p = thresholds_for_review_capacity(
            state.artifact.validation_risks, capacity
        )
        st.caption(
            f"Validation percentiles: Automatic p{automatic_p:.1f}; "
            f"Human Review cutoff p{assisted_p:.1f}. Default 30/100 maps to p70/p90."
        )
        st.caption("Exploratory for this case only; canonical reported results stay unchanged.")
        return reroute_case_record(record, thresholds, state.artifact.system.weights)
    return record


def render_result(
    record: DecisionRecord, *, state: DemoState | None = None, synthetic: bool = False
) -> None:
    """Display a human-readable route, component scores, and checked explanation."""
    if state is not None:
        record = render_review_capacity(record, state)
    label = record.predicted_label
    if record.level is DecisionLevel.AUTOMATIC:
        st.success(f"\U0001f7e2 Automatic: the model leans {label}.")
        st.write(
            "The research policy returned this case in its Automatic tier. This is not a diagnosis."
        )
    elif record.level is DecisionLevel.ASSISTED:
        st.warning(
            f"\U0001f7e1 Assisted: the model leans {label}; additional verification is advised."
        )
    else:
        st.error(
            f"\U0001f534 Human Review: the model leans {label}; a human should review this case."
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
        f"Automatic through {record.automatic_threshold:.3f} | "
        f"Assisted through {record.assisted_threshold:.3f} | "
        f"Human Review above {record.assisted_threshold:.3f}."
    )
    st.markdown(
        f"<div role='img' aria-label='Risk gauge: {record.risk:.3f}. "
        f"Automatic threshold {record.automatic_threshold:.3f}; "
        f"Human Review starts above {record.assisted_threshold:.3f}.' "
        "style='position:relative;height:8px;background:#d9dee7;border-radius:5px'>"
        f"<div style='width:{np.clip(record.risk, 0, 1) * 100:.2f}%;height:8px;"
        "background:#315b8a;border-radius:5px'></div>"
        "<span aria-hidden='true' style='position:absolute;left:"
        f"{record.automatic_threshold * 100:.2f}%;top:-3px;height:14px;width:2px;"
        "background:#111'></span>"
        "<span aria-hidden='true' style='position:absolute;left:"
        f"{record.assisted_threshold * 100:.2f}%;top:-3px;height:14px;width:2px;"
        "background:#111'></span></div>",
        unsafe_allow_html=True,
    )

    explanation = generate_explanation(record)
    check = check_explanation(record, explanation)
    with st.expander("Grounded explanation and checker"):
        st.write(explanation)
        if check.passed:
            st.success("Rule-based checker passed.")
        else:
            st.error("Checker issues: " + ", ".join(check.issues))

    with st.popover("Glossary"):
        for term, definition in GLOSSARY.items():
            st.markdown(f"**{term}** - {definition}")
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
        render_result(record, state=state)


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
                f"Typical TRAIN range (5th-95th percentile): {p05:.3g} to {p95:.3g}. "
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
            render_result(record, state=state)


def _batch_output_csv(batch) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(("row", "model_leans", "decision", "risk", "reason", "warnings"))
    for item in batch:
        record = item.record
        writer.writerow(
            (
                item.row_number,
                record.predicted_label,
                record.level.value,
                f"{record.risk:.6f}",
                record.referral_reason or "No single contributor triggered referral",
                " | ".join(record.input_warnings),
            )
        )
    return stream.getvalue()


def render_csv_batch(state: DemoState) -> None:
    st.header("Upload or paste a WDBC CSV")
    st.write(
        "Each row needs all 30 numeric cell-nucleus features. "
        "No ID or demographic columns are accepted."
    )
    st.download_button(
        "Download blank 30-feature CSV template",
        data=csv_template(state.data.feature_names),
        file_name="raa_wdbc_template.csv",
        mime="text/csv",
    )
    uploaded = st.file_uploader("Choose a CSV file", type=("csv",), key="batch_csv_upload")
    pasted = st.text_area("Or paste CSV text", height=160, key="batch_csv_paste")
    st.caption("Maximum 100 rows per batch. Uploaded and pasted values stay in memory only.")
    if st.button("Run batch triage", type="primary"):
        source = pasted if pasted.strip() else ""
        if not source and uploaded is not None:
            try:
                source = uploaded.getvalue().decode("utf-8-sig")
            except UnicodeDecodeError:
                st.error("Could not read this file as UTF-8 CSV. Save it as UTF-8 and try again.")
                return
        try:
            batch = predict_csv(source, context=state.artifact.inference_context)
        except CaseInputError as error:
            st.error(str(error))
            return
        st.session_state["batch_triage_output"] = _batch_output_csv(batch)
        counts = {level: 0 for level in ("Automatic", "Assisted", "Human Review")}
        table_rows = []
        for item in batch:
            record = item.record
            counts[record.level.value] += 1
            table_rows.append(
                {
                    "Row": item.row_number,
                    "Model leans": record.predicted_label,
                    "Decision": record.level.value,
                    "Risk": round(record.risk, 3),
                    "Reason": record.referral_reason or "No single contributor triggered referral",
                    "Input warning": "; ".join(record.input_warnings),
                }
            )
        st.session_state["batch_triage_table"] = table_rows
        st.session_state["batch_triage_counts"] = counts
    if "batch_triage_table" in st.session_state:
        table_rows = st.session_state["batch_triage_table"]
        counts = st.session_state["batch_triage_counts"]
        st.subheader(f"Triage results ? {len(table_rows)} rows")
        st.table(table_rows)
        columns = st.columns(3)
        for column, level, icon in zip(
            columns,
            ("Automatic", "Assisted", "Human Review"),
            ("\U0001f7e2", "\U0001f7e1", "\U0001f534"),
            strict=True,
        ):
            percent = counts[level] / len(table_rows) * 100
            column.metric(
                f"{icon} {level}", f"{percent:.1f}%", f"{counts[level]} of {len(table_rows)}"
            )
        st.download_button(
            "Download triage results",
            data=st.session_state["batch_triage_output"],
            file_name="raa_triage_results.csv",
            mime="text/csv",
        )


def render_what_if(state: DemoState) -> None:
    """Live what-if on a held-out row, with a paper-recipe synthetic shift option."""
    st.header("What-if: adjust four measurements")
    st.write("Start from a held-out WDBC test example, then move four sliders.")
    keys = tuple(state.examples)
    example_key = st.selectbox(
        "Held-out starting case",
        keys,
        format_func=lambda key: state.examples[key].title,
        key="what_if_example",
    )
    case = state.examples[example_key]
    original = state.data.features[case.dataset_row].copy()
    row_key = f"what_if_base_{example_key}"
    synthetic_key = f"what_if_is_synthetic_{example_key}"
    selected_key = f"what_if_shifted_indices_{example_key}"
    if row_key in st.session_state:
        original = np.asarray(st.session_state[row_key], dtype=np.float64).copy()
    is_synthetic = bool(st.session_state.get(synthetic_key, False))
    feature_indices = [
        state.data.feature_names.index(name) for name in state.artifact.guided_features[:4]
    ]
    widget_keys = [f"what_if_{example_key}_{index}" for index in feature_indices]
    current = original.copy()
    for index, widget_key in zip(feature_indices, widget_keys, strict=True):
        current[index] = float(st.session_state.get(widget_key, current[index]))

    make_col, reset_col = st.columns(2)
    if make_col.button("Make it unusual (synthetic)", type="primary"):
        config = load_config()
        anomaly = config["anomaly"]
        del anomaly
        stress = config["stress_test"]
        shifted, changed = synthetic_shift_case(
            current,
            state.artifact.system.anomaly_scaler.scale_,
            feature_count=int(stress["feature_count"]),
            shift_sigma=float(stress["shift_magnitude_sigma"]),
            seed=int(stress["seed"]),
        )
        st.session_state[row_key] = shifted
        st.session_state[synthetic_key] = True
        st.session_state[selected_key] = changed
        for index, widget_key in zip(feature_indices, widget_keys, strict=True):
            st.session_state[widget_key] = float(shifted[index])
        st.rerun()
    if reset_col.button("Reset to held-out example", key=f"reset_{example_key}"):
        st.session_state.pop(row_key, None)
        st.session_state[synthetic_key] = False
        st.session_state.pop(selected_key, None)
        for widget_key in widget_keys:
            st.session_state.pop(widget_key, None)
        st.rerun()

    train = state.data.features[state.split.train]
    sliders = st.columns(2)
    for position, (index, widget_key) in enumerate(zip(feature_indices, widget_keys, strict=True)):
        feature = state.data.feature_names[index]
        sigma = float(state.artifact.system.anomaly_scaler.scale_[index])
        lower = max(0.0, float(train[:, index].min()) - 3 * sigma)
        upper = float(train[:, index].max()) + 3 * sigma
        with sliders[position % 2]:
            st.slider(
                feature.title(),
                min_value=lower,
                max_value=upper,
                value=float(current[index]),
                key=widget_key,
                help="This changes one measured feature and reruns the actual model pipeline.",
            )
    for index, widget_key in zip(feature_indices, widget_keys, strict=True):
        current[index] = float(st.session_state[widget_key])
    if is_synthetic:
        changed_names = [
            state.data.feature_names[index] for index in st.session_state[selected_key]
        ]
        st.caption("Synthetic shifted fields: " + ", ".join(changed_names))
    record = predict_case(
        current,
        np.ones(current.size, dtype=bool),
        context=state.artifact.inference_context,
    )
    render_result(record, state=state, synthetic=is_synthetic)


def render_why_abstain() -> None:
    results = load_paper_results()
    pooled = results["pooled_case_metrics"]
    levels = results["pooled_decision_level_metrics"]
    st.header("Why does the system abstain?")
    st.write(
        "The policy routes uncertain, unusual, or higher-consequence cases for additional review. "
        "These aggregate values are loaded from the canonical 30-split results file."
    )
    st.caption(f"Run ID: {results['run_id']} | {results['test_cases']:,} held-out records")
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
        page_title="Risk-Aware Abstention",
        page_icon="\U0001f9ed",
        layout="wide",
    )
    st.title("Risk-Aware Abstention")
    st.error(BANNER)
    st.caption(PRIVACY)
    st.sidebar.caption("Local research demo; no names or demographic fields")
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
    elif mode == "Upload CSV":
        render_csv_batch(state)
    elif mode == "What-if":
        render_what_if(state)
    elif mode == "Why abstain?":
        render_why_abstain()
    else:
        st.info("This mode is being prepared; choose Example cases for the working one-click demo.")


if __name__ == "__main__":
    main()
