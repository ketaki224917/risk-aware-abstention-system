"""Simple questionnaire interface backed by UCI mammogram report features."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import streamlit as st

from raa.app.copy import (
    INTAKE_HISTORY_OPTIONS,
    INTAKE_SYMPTOM_OPTIONS,
    INTAKE_SYMPTOM_QUESTIONS,
    PRIVACY,
)
from raa.app.report import build_prediction_report
from raa.explain.llm_adapter import LLMUnavailableError, generate_prediction_narrative
from raa.mammography import (
    DEFAULT_ARTIFACT_DIR,
    DENSITY_CODES,
    MARGIN_CODES,
    SHAPE_CODES,
    MammographyArtifact,
    explain_mammography_case,
    load_mammography_artifact,
    predict_mammography_case,
)
from raa.risk.policy import DecisionLevel

APP_TITLE = "Risk Aware Abstention System"


@st.cache_data
def _load_evaluation() -> dict[str, Any]:
    return json.loads((DEFAULT_ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))


@st.cache_resource(show_spinner="Loading the saved model...")
def _load_model() -> MammographyArtifact:
    return load_mammography_artifact()


def _report_code(label: str | None, options: dict[str, int]) -> int | None:
    return options.get(label) if label is not None else None


def _current_answers() -> dict[str, Any]:
    return {
        "age": st.session_state.get("health_age"),
        "height_cm": st.session_state.get("health_height_cm"),
        "weight_kg": st.session_state.get("health_weight_kg"),
        "gender": st.session_state.get("health_gender"),
        "family_history": st.session_state.get("health_family_history"),
        "medical_history": st.session_state.get("health_medical_history"),
        "report_available": st.session_state.get("health_report_available"),
        "shape": st.session_state.get("health_shape"),
        "margin": st.session_state.get("health_margin"),
        "density": st.session_state.get("health_density"),
        **{key: st.session_state.get(f"health_{key}") for key, _, _ in INTAKE_SYMPTOM_QUESTIONS},
    }


def _render_form() -> dict[str, Any]:
    st.write(
        "Answer the health questions. If you have a mammogram report, enter its mass findings."
    )
    st.caption(
        "Age and mammogram findings affect the model estimate. "
        "Height, weight, gender, symptoms, and history are included as report context."
    )
    with st.expander("Privacy"):
        st.write(PRIVACY)
    with st.container(border=True):
        st.subheader("Basic health")
        basics_left, basics_right = st.columns(2)
        with basics_left:
            st.number_input(
                "Age when the mammogram was taken (years)",
                min_value=1,
                max_value=120,
                value=None,
                step=1,
                placeholder="Age",
                key="health_age",
            )
        with basics_right:
            st.selectbox(
                "Gender",
                options=("Woman", "Man", "Non-binary", "Prefer not to say"),
                index=None,
                placeholder="Choose an answer",
                key="health_gender",
            )
        basics_left, basics_right = st.columns(2)
        with basics_left:
            st.number_input(
                "Height (cm)",
                min_value=50,
                max_value=250,
                value=None,
                step=1,
                placeholder="Height",
                key="health_height_cm",
            )
        with basics_right:
            st.number_input(
                "Weight (kg)",
                min_value=10,
                max_value=350,
                value=None,
                step=1,
                placeholder="Weight",
                key="health_weight_kg",
            )
        st.selectbox(
            "Has a close family member had breast cancer?",
            options=INTAKE_HISTORY_OPTIONS,
            index=None,
            placeholder="Choose Yes, No, or Not sure",
            key="health_family_history",
        )
        st.selectbox(
            "Have you had a previous breast condition, biopsy, or treatment?",
            options=INTAKE_HISTORY_OPTIONS,
            index=None,
            placeholder="Choose Yes, No, or Not sure",
            key="health_medical_history",
        )

        st.divider()
        st.subheader("Breast health questions")
        st.caption("Choose Yes, No, or Not sure for each question.")
        columns = st.columns(2)
        for index, (key, question, _) in enumerate(INTAKE_SYMPTOM_QUESTIONS):
            with columns[index % 2]:
                st.selectbox(
                    question,
                    options=INTAKE_SYMPTOM_OPTIONS,
                    index=None,
                    placeholder="Choose an answer",
                    key=f"health_{key}",
                )

        st.divider()
        report_available = st.selectbox(
            "Do you have a mammogram report with a mass finding?",
            options=("Yes", "No"),
            index=None,
            placeholder="Choose Yes or No",
            key="health_report_available",
        )
        if report_available == "Yes":
            st.markdown("**Find these details in the report**")
            st.caption(
                "If the report does not give a clear value, select Not sure. "
                "The model uses age and these three report fields."
            )
            shape_options = ("Not sure", *SHAPE_CODES)
            margin_options = ("Not sure", *MARGIN_CODES)
            density_options = ("Not sure", *DENSITY_CODES)
            left, middle, right = st.columns(3)
            with left:
                st.selectbox(
                    "Mass shape",
                    options=shape_options,
                    index=None,
                    placeholder="Choose a report value",
                    help="Round, oval, lobulated, or irregular.",
                    key="health_shape",
                )
            with middle:
                st.selectbox(
                    "Mass edge (margin)",
                    options=margin_options,
                    index=None,
                    placeholder="Choose a report value",
                    help=(
                        "The report may say circumscribed, microlobulated, obscured, "
                        "ill-defined, or spiculated."
                    ),
                    key="health_margin",
                )
            with right:
                st.selectbox(
                    "Mass density",
                    options=density_options,
                    index=None,
                    placeholder="Choose a report value",
                    help="High, similar to nearby tissue, low, or mostly fat-containing.",
                    key="health_density",
                )

    return _current_answers()


def _prediction_facts(
    answers: dict[str, Any],
    record: Any | None,
    explanations: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "model_output": record.predicted_label.title()
        if record is not None
        else "No class estimate",
        "route": record.level.value if record is not None else "Human Review",
        "risk_score": f"{record.risk:.3f}" if record is not None else "not computed",
        "risk_reason": record.referral_reason
        if record is not None
        else "No mammogram report was provided",
        "explanations": list(explanations),
        "age": answers.get("age"),
        "height_cm": answers.get("height_cm"),
        "weight_kg": answers.get("weight_kg"),
        "gender": answers.get("gender"),
        "report_findings": {
            "shape": answers.get("shape"),
            "margin": answers.get("margin"),
            "density": answers.get("density"),
        },
        "family_history": answers.get("family_history"),
        "medical_history": answers.get("medical_history"),
        "symptoms": {short: answers.get(key) for key, _, short in INTAKE_SYMPTOM_QUESTIONS},
    }


def _render_report(submission: dict[str, Any]) -> None:
    if st.button("Generate prediction report", type="primary", key="generate_prediction_report"):
        record = submission["record"]
        facts = _prediction_facts(submission["answers"], record, submission["explanations"])
        try:
            with st.spinner("Preparing your report..."):
                narrative = generate_prediction_narrative(facts).text
        except LLMUnavailableError:
            narrative = (
                f"The model output is {facts['model_output']} and the RAA route is "
                f"{facts['route']}. The explanation and scores below are the recorded model output."
            )
        report = build_prediction_report(
            answers=submission["answers"],
            record=record,
            explanations=submission["explanations"],
            narrative=narrative,
            evaluation=_load_evaluation(),
        )
        st.session_state["prediction_report"] = {
            "answers": submission["answers"],
            "text": report,
        }

    report = st.session_state.get("prediction_report")
    if report is not None and report["answers"] == submission["answers"]:
        st.success("Your report is ready.")
        st.download_button(
            "Download prediction report",
            data=report["text"],
            file_name="risk_aware_prediction_report.txt",
            mime="text/plain",
            key="prediction_report_download",
        )


def _render_prediction(submission: dict[str, Any]) -> None:
    record = submission["record"]
    if record is None:
        st.error("\U0001f534 Human Review - no benign/malignant estimate")
        st.write(
            "Symptoms and history alone do not match the model's training data. "
            "No class estimate was produced."
        )
        st.caption("A clinician should interpret symptoms and any mammogram findings.")
        _render_report(submission)
        return

    if record.level is DecisionLevel.AUTOMATIC:
        st.success(f"\U0001f7e2 Automatic - the model leans {record.predicted_label}.")
    elif record.level is DecisionLevel.ASSISTED:
        st.warning(
            f"\U0001f7e1 Assisted - the model leans {record.predicted_label}; review is needed."
        )
    else:
        st.error(f"\U0001f534 Human Review - unverified model lean is {record.predicted_label}.")
        if record.referral_reason:
            st.write(f"Reason: {record.referral_reason.replace('_', ' ')}.")

    st.caption("This estimates a mammographic mass label. It is not a diagnosis.")
    if record.estimated_feature_count:
        st.info(
            f"{record.measured_feature_count} of 4 inputs measured; "
            f"{record.estimated_feature_count} estimated from TRAIN data. "
            "The route is Human Review because report details are incomplete."
        )
    for warning in record.input_warnings:
        st.warning(warning)

    st.subheader("Why the model leaned this way")
    for explanation in submission["explanations"]:
        st.write(f"- {explanation}")

    with st.expander("How the RAA route was chosen"):
        st.caption(
            "Risk signals used by the route; these are model scores, not cancer probabilities."
        )
        columns = st.columns(3)
        for column, title, value in zip(
            columns,
            ("Model disagreement", "Unusualness", "Cost of error"),
            (record.uncertainty, record.anomaly, record.consequence),
            strict=True,
        ):
            column.progress(int(np.clip(value, 0, 1) * 100), text=f"{title}: {value:.2f}")
        st.progress(int(np.clip(record.risk, 0, 1) * 100), text=f"Combined risk: {record.risk:.3f}")
        st.caption(
            f"Automatic through {record.automatic_threshold:.3f}; "
            f"Assisted through {record.assisted_threshold:.3f}; "
            f"above that is Human Review."
        )
        st.latex(r"R = 0.5U + 0.2A + 0.3C")
        st.caption(
            "The thresholds and consequence values are project settings. "
            "The model score is not a calibrated chance of cancer."
        )

    with st.expander("About this model"):
        st.write(
            "It was trained on UCI's Mammographic Mass dataset using age, mass shape, "
            "mass edge, and density from mammogram records. Symptoms and family history are "
            "included in the report but do not change the model score."
        )
        test = _load_evaluation()["test"]
        automatic_false_negatives = (
            test["malignant_false_negatives"] - test["malignant_false_negatives_routed_away"]
        )
        st.write(
            f"On its held-out test split, accuracy was {test['accuracy']:.1%}, "
            f"malignant sensitivity was {test['sensitivity_malignant']:.1%}, and "
            f"benign specificity was {test['specificity_benign']:.1%}."
        )
        st.write(
            f"At p70/p90, the Automatic tier error rate was {test['automatic_error_rate']:.1%}; "
            f"{automatic_false_negatives} of "
            f"{test['malignant_false_negatives']} malignant false negatives were in it."
        )
        st.caption("These held-out values do not establish clinical performance.")

    _render_report(submission)


def render_mammography_intake() -> None:
    """Render the single user-facing questionnaire and prediction result."""
    try:
        artifact = _load_model()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    answers = _render_form()
    if st.button("Get result", type="primary", key="health_submit"):
        st.session_state.pop("health_submission", None)
        st.session_state.pop("prediction_report", None)
        required = (
            "age",
            "height_cm",
            "weight_kg",
            "gender",
            "family_history",
            "medical_history",
            "report_available",
            *[key for key, _, _ in INTAKE_SYMPTOM_QUESTIONS],
        )
        if any(answers.get(key) is None for key in required):
            st.error("Complete the basic health questions and choose an answer for each symptom.")
            return
        if not float(answers["age"]).is_integer():
            st.error("Enter age as a whole number of years.")
            return
        if answers["report_available"] == "Yes" and any(
            answers.get(key) is None for key in ("shape", "margin", "density")
        ):
            st.error("Choose a report value or Not sure for shape, edge, and density.")
            return

        if answers["report_available"] == "No":
            record = None
            explanations: tuple[str, ...] = ()
        else:
            values = {
                "Age": int(answers["age"]),
                "Shape": _report_code(answers["shape"], SHAPE_CODES),
                "Margin": _report_code(answers["margin"], MARGIN_CODES),
                "Density": _report_code(answers["density"], DENSITY_CODES),
            }
            try:
                record = predict_mammography_case(values, artifact)
                explanations = explain_mammography_case(values, record, artifact)
            except ValueError as error:
                st.error(str(error))
                return
        st.session_state["health_submission"] = {
            "answers": answers,
            "record": record,
            "explanations": explanations,
        }

    submission = st.session_state.get("health_submission")
    if submission is not None and submission["answers"] == answers:
        st.divider()
        _render_prediction(submission)
