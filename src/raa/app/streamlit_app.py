"""Breast-health questionnaire and WDBC research interface for the local RAA prototype."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

import numpy as np
import streamlit as st

from raa.app.copy import (
    BANNER,
    GLOSSARY,
    INPUT_HELP,
    INTAKE_AGE_ERROR,
    INTAKE_AGE_LABEL,
    INTAKE_BASIC_LABEL,
    INTAKE_GENDER_LABEL,
    INTAKE_GENDER_OPTIONS,
    INTAKE_HEIGHT_LABEL,
    INTAKE_HISTORY_OPTIONS,
    INTAKE_HISTORY_QUESTION,
    INTAKE_INTRO,
    INTAKE_LLM_FALLBACK,
    INTAKE_LLM_NOTE,
    INTAKE_MEASUREMENTS_ERROR,
    INTAKE_MISSING,
    INTAKE_MODEL_LIMIT,
    INTAKE_REASON,
    INTAKE_REPORT_LABEL,
    INTAKE_RESULT,
    INTAKE_SCOPE,
    INTAKE_SUBMIT,
    INTAKE_SYMPTOM_OPTIONS,
    INTAKE_SYMPTOM_QUESTIONS,
    INTAKE_SYMPTOMS_LABEL,
    INTAKE_TITLE,
    INTAKE_WEIGHT_LABEL,
    LIMITS,
    PRIVACY,
)
from raa.app.demo_assets import DemoArtifact, load_demo_artifact, load_paper_results
from raa.app.examples import ExampleCase, select_example_cases
from raa.app.report import build_intake_report
from raa.config import load_config
from raa.data import BreastCancerData, DataSplit, load_breast_cancer_data, stratified_split
from raa.explain.checker import check_explanation
from raa.explain.llm_adapter import LLMUnavailableError, generate_intake_status_summary
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
        "Enter six mean measurements from one compatible WDBC record. "
        "The remaining 24 are estimated by a KNN imputer fitted on TRAIN only."
    )
    st.caption(
        "Number boxes start blank. Move a slider to provide its value; each slider thumb "
        "starts at the TRAIN median only as a visual guide and is not used unless moved."
    )
    st.markdown("**6 of 30 measured, 24 estimated**")
    train = state.data.features[state.split.train]
    values: dict[str, float | None] = {}
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
                st.session_state[number_key] = None
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
                    placeholder="Type a measured value",
                    required=True,
                    on_change=_sync_slider_from_number,
                    args=(slider_key, number_key, low, high),
                )
            number_value = st.session_state[number_key]
            values[feature] = None if number_value is None else float(number_value)
    if st.button("Assess these six measurements", type="primary"):
        missing = [feature for feature, value in values.items() if value is None]
        if missing:
            st.error("Enter a value for all six measurements using number boxes or sliders.")
        else:
            row = np.full(len(state.data.feature_names), np.nan, dtype=np.float64)
            measured = np.zeros(row.size, dtype=bool)
            for feature, value in values.items():
                if value is None:
                    continue
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


def render_visual_style() -> None:
    """Apply a high-contrast dark theme across the intake and research pages."""
    st.markdown(
        """
        <style>
          .stApp, [data-testid="stAppViewContainer"] {
            background: radial-gradient(ellipse at top, #16233c 0, #0b1220 58rem);
            color: #f8fafc;
          }
          [data-testid="stHeader"] { background: rgba(11,18,32,.96); }
          [data-testid="stSidebar"] {
            background: #101a2c; border-right: 1px solid #334155;
          }
          .block-container { max-width: 980px; padding-top: 1.5rem; }
          h1, h2, h3, h4 { color: #f8fafc !important; letter-spacing: -.015em; }
          p, [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
          label, .stCaption, .stCaption p {
            color: #e2e8f0 !important;
          }
          [data-testid="stWidgetLabel"] p { color: #f8fafc !important; font-weight: 650; }
          [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #334761; border-radius: 18px;
            background: rgba(20,32,52,.96); box-shadow: 0 10px 32px rgba(0,0,0,.24);
          }
          [data-testid="stAlert"] {
            border: 1px solid #405675; border-radius: 14px;
            background: #18263c;
          }
          [data-testid="stAlert"] p, [data-testid="stAlert"] div {
            color: #f1f5f9 !important;
          }
          input, textarea, [data-baseweb="select"] > div {
            background: #0b1424 !important; color: #f8fafc !important;
            border-color: #64748b !important; border-radius: 10px !important;
          }
          [data-baseweb="select"] div, [data-baseweb="select"] input {
            color: #f8fafc !important;
          }
          [role="listbox"], [role="option"] {
            background: #132139 !important; color: #f8fafc !important;
          }
          .stButton > button[kind="primary"] {
            border-radius: 12px; min-height: 2.8rem; font-weight: 750;
            background: #22d3ee; border-color: #22d3ee; color: #07111f !important;
          }
          .stButton > button[kind="primary"]:hover {
            background: #67e8f9; border-color: #67e8f9;
          }
          input::placeholder { color: #9eacc0 !important; opacity: 1; }
          :focus-visible { outline: 3px solid #fbbf24 !important; outline-offset: 2px; }
          hr { border-color: #334155; }
          @media (max-width: 640px) { .block-container { padding: 1rem 1rem 2rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_health_questionnaire() -> None:
    """Collect basic details and symptom answers without making unsupported predictions."""
    st.header(INTAKE_TITLE)
    st.write(INTAKE_INTRO)
    st.info(INTAKE_MODEL_LIMIT)
    st.caption(INTAKE_LLM_NOTE)
    with st.container(border=True):
        st.subheader(INTAKE_BASIC_LABEL)
        age_col, height_col, weight_col = st.columns(3)
        with age_col:
            age = st.number_input(
                INTAKE_AGE_LABEL,
                min_value=1,
                max_value=120,
                value=None,
                step=1,
                format="%d",
                placeholder="Age",
                key="intake_age",
                required=True,
            )
        with height_col:
            height = st.number_input(
                INTAKE_HEIGHT_LABEL,
                min_value=50,
                max_value=250,
                value=None,
                step=1,
                placeholder="Height",
                key="intake_height",
                required=True,
            )
        with weight_col:
            weight = st.number_input(
                INTAKE_WEIGHT_LABEL,
                min_value=1.0,
                max_value=300.0,
                value=None,
                step=0.1,
                format="%.1f",
                placeholder="Weight",
                key="intake_weight",
                required=True,
            )

        gender_col, history_col = st.columns(2)
        with gender_col:
            gender = st.selectbox(
                INTAKE_GENDER_LABEL,
                options=INTAKE_GENDER_OPTIONS,
                index=None,
                placeholder="Select an option",
                key="intake_gender",
            )
        with history_col:
            history = st.selectbox(
                INTAKE_HISTORY_QUESTION,
                options=INTAKE_HISTORY_OPTIONS,
                index=None,
                placeholder="Select an option",
                key="intake_history",
            )

        st.divider()
        st.subheader(INTAKE_SYMPTOMS_LABEL)
        st.caption("Choose Yes, No, or Not sure for each question.")
        symptom_answers: dict[str, str | None] = {}
        symptom_columns = st.columns(2)
        for index, (answer_key, question, short_label) in enumerate(INTAKE_SYMPTOM_QUESTIONS):
            with symptom_columns[index % 2]:
                symptom_answers[answer_key] = st.selectbox(
                    question,
                    options=INTAKE_SYMPTOM_OPTIONS,
                    index=None,
                    placeholder=f"{short_label}: select an option",
                    key=f"intake_{answer_key}",
                )

    current_answers: dict[str, str | float | int | None] = {
        "age": age,
        "height_cm": height,
        "weight_kg": weight,
        "gender": gender,
        "history": history,
        **symptom_answers,
    }
    if st.button(INTAKE_SUBMIT, type="primary"):
        st.session_state.pop("intake_submission", None)
        if any(answer is None for answer in current_answers.values()):
            st.error(INTAKE_MISSING)
            return
        if not np.isfinite(float(age)) or not float(age).is_integer() or not 1 <= age <= 120:
            st.error(INTAKE_AGE_ERROR)
            return
        if not 50 <= height <= 250 or not 1 <= weight <= 300:
            st.error(INTAKE_MEASUREMENTS_ERROR)
            return

        report_answers = {
            "age": str(int(age)),
            "height_cm": str(int(height)),
            "weight_kg": f"{float(weight):g}",
            "gender": str(gender),
            "history": str(history),
            **{key: str(value) for key, value in symptom_answers.items()},
        }
        try:
            with st.spinner("Drafting a status explanation with the local LLM..."):
                local_summary = generate_intake_status_summary()
            summary = local_summary.text
            source = f"Local Ollama model: {local_summary.model} (exploratory, not evaluated)"
            generated_by_llm = True
        except LLMUnavailableError:
            summary = INTAKE_LLM_FALLBACK
            source = "Fixed safe fallback (local LLM unavailable or summary rejected)"
            generated_by_llm = False
        report = build_intake_report(
            report_answers,
            explanation=summary,
            explanation_source=source,
        )
        st.session_state["intake_submission"] = {
            "answers": current_answers,
            "summary": summary,
            "source": source,
            "generated_by_llm": generated_by_llm,
            "report": report,
        }

    submission = st.session_state.get("intake_submission")
    if submission is None or submission["answers"] != current_answers:
        return
    st.error(INTAKE_RESULT)
    st.info(INTAKE_REASON)
    st.caption(INTAKE_SCOPE)
    st.subheader("LLM explanation")
    st.write(submission["summary"])
    if submission["generated_by_llm"]:
        st.caption(
            f"Generated locally by {submission['source']}. The LLM did not receive your answers "
            "and cannot change the result."
        )
    else:
        st.warning(
            "The local LLM was unavailable or returned text that failed the safety checks. "
            "This report uses a fixed explanation instead."
        )
    st.download_button(
        INTAKE_REPORT_LABEL,
        data=submission["report"],
        file_name="risk_aware_intake_result_report.txt",
        mime="text/plain",
        key="intake_report_download",
    )


def main() -> None:
    st.set_page_config(
        page_title="Risk-Aware Abstention",
        page_icon="\U0001f9ed",
        layout="wide",
    )
    render_visual_style()
    st.title("Risk-Aware Abstention")
    st.warning(BANNER)
    st.caption(PRIVACY)
    st.sidebar.caption("Health answers stay local and are not used by the current model.")
    mode = st.sidebar.radio(
        "Choose a mode",
        (
            INTAKE_TITLE,
            "Guided entry",
            "Upload CSV",
            "What-if",
            "Example cases",
            "Why abstain?",
        ),
        index=0,
    )
    if mode == INTAKE_TITLE:
        render_health_questionnaire()
        return
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
        st.info("Choose a mode from the sidebar.")


if __name__ == "__main__":
    main()
