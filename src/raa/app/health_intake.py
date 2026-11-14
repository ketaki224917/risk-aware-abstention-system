"""Simple report-entry interface backed by the saved UCI mammography RAA model."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import streamlit as st

from raa.app.copy import (
    AGE_LABEL,
    DENSITY_CHOICES,
    DENSITY_HELP,
    DENSITY_QUESTION,
    INPUT_HELP,
    INPUT_INTRO,
    MARGIN_CHOICES,
    MARGIN_HELP,
    MARGIN_QUESTION,
    MODEL_INPUTS_COPY,
    NO_ESTIMATE_COPY,
    PRIVACY,
    REPORT_DETAILS_NOTE,
    REPORT_HAS_MASS,
    REPORT_NO_MASS,
    REPORT_STATUS_LABEL,
    REPORT_STATUS_OPTIONS,
    SHAPE_CHOICES,
    SHAPE_HELP,
    SHAPE_QUESTION,
    UNKNOWN_REPORT_VALUE,
)
from raa.app.docx_report import build_prediction_report_docx
from raa.app.report import build_prediction_report
from raa.explain.llm_adapter import LLMUnavailableError, generate_prediction_narrative
from raa.mammography import (
    DEFAULT_ARTIFACT_DIR,
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
    """Collect only the fields needed to run or report this model."""
    status = st.session_state.get("health_report_status")
    has_mass = status == REPORT_HAS_MASS
    return {
        "report_status": status,
        "age": st.session_state.get("health_age") if has_mass else None,
        "shape": st.session_state.get("health_shape") if has_mass else None,
        "margin": st.session_state.get("health_margin") if has_mass else None,
        "density": st.session_state.get("health_density") if has_mass else None,
    }


def _render_form() -> dict[str, Any]:
    st.write(INPUT_INTRO)
    st.caption(INPUT_HELP)
    with st.expander("Privacy"):
        st.write(PRIVACY)

    with st.container(border=True):
        st.subheader("Mammogram report")
        status = st.selectbox(
            REPORT_STATUS_LABEL,
            options=REPORT_STATUS_OPTIONS,
            index=None,
            placeholder="Choose an answer",
            key="health_report_status",
        )
        if status == REPORT_HAS_MASS:
            st.info(REPORT_DETAILS_NOTE)
            st.number_input(
                AGE_LABEL,
                min_value=1,
                max_value=120,
                value=None,
                step=1,
                placeholder="Age",
                key="health_age",
            )
            st.selectbox(
                SHAPE_QUESTION,
                options=(UNKNOWN_REPORT_VALUE, *SHAPE_CHOICES),
                index=None,
                placeholder="Choose the report wording",
                help=SHAPE_HELP,
                key="health_shape",
            )
            st.selectbox(
                MARGIN_QUESTION,
                options=(UNKNOWN_REPORT_VALUE, *MARGIN_CHOICES),
                index=None,
                placeholder="Choose the report wording",
                help=MARGIN_HELP,
                key="health_margin",
            )
            st.selectbox(
                DENSITY_QUESTION,
                options=(UNKNOWN_REPORT_VALUE, *DENSITY_CHOICES),
                index=None,
                placeholder="Choose the report wording",
                help=DENSITY_HELP,
                key="health_density",
            )

    return _current_answers()


def _prediction_facts(
    answers: dict[str, Any],
    record: Any | None,
    explanations: tuple[str, ...],
) -> dict[str, Any]:
    if record is not None:
        reason = record.referral_reason
    elif answers.get("report_status") == REPORT_NO_MASS:
        reason = "The report does not describe a mammographic mass"
    else:
        reason = "No compatible mammogram mass report was supplied"
    return {
        "model_output": record.predicted_label.title()
        if record is not None
        else "No class estimate",
        "route": record.level.value if record is not None else "Human Review",
        "risk_score": f"{record.risk:.3f}" if record is not None else "not computed",
        "risk_reason": reason,
        "explanations": list(explanations),
        "report_status": answers.get("report_status"),
        "age": answers.get("age"),
        "report_findings": {
            "shape": answers.get("shape"),
            "edge": answers.get("margin"),
            "density": answers.get("density"),
        },
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
                f"{facts['route']}. The report lists the supplied model-compatible fields."
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
            "docx": build_prediction_report_docx(report),
        }

    report = st.session_state.get("prediction_report")
    if report is not None and report["answers"] == submission["answers"]:
        st.success("Your report is ready.")
        st.download_button(
            "Download Word report",
            data=report["docx"],
            file_name="risk_aware_prediction_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="prediction_report_download",
        )


def _render_prediction(submission: dict[str, Any]) -> None:
    record = submission["record"]
    if record is None:
        st.error("\U0001f534 Human Review - no benign/malignant estimate")
        st.write(NO_ESTIMATE_COPY)
        if submission["answers"].get("report_status") == REPORT_NO_MASS:
            st.caption("The entered report did not describe a mass for this model to assess.")
        else:
            st.caption("The app needs the report details before it can run its saved model.")
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
            f"{record.measured_feature_count} of 4 model inputs measured; "
            f"{record.estimated_feature_count} estimated from TRAIN data. "
            "Incomplete report details require Human Review."
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
            "above that is Human Review."
        )
        st.latex(r"R = 0.5U + 0.2A + 0.3C")
        st.caption(
            "The thresholds and consequence values are project settings. "
            "The model score is not a calibrated chance of cancer."
        )

    with st.expander("About this model"):
        st.write(MODEL_INPUTS_COPY)
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
    """Render the single user-facing report-entry questionnaire."""
    try:
        artifact = _load_model()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    answers = _render_form()
    if st.button("Get result", type="primary", key="health_submit"):
        st.session_state.pop("health_submission", None)
        st.session_state.pop("prediction_report", None)

        status = answers.get("report_status")
        if status is None:
            st.error("Choose whether the mammogram report describes a mass.")
            return

        if status != REPORT_HAS_MASS:
            record = None
            explanations: tuple[str, ...] = ()
        else:
            if answers.get("age") is None or any(
                answers.get(key) is None for key in ("shape", "margin", "density")
            ):
                st.error(
                    "Enter the scan age and choose a report option for shape, edge, and density. "
                    "Select Not sure / not listed when a report detail is unclear."
                )
                return
            if not float(answers["age"]).is_integer():
                st.error("Enter age as a whole number of years.")
                return

            values = {
                "Age": int(answers["age"]),
                "Shape": _report_code(answers["shape"], SHAPE_CHOICES),
                "Margin": _report_code(answers["margin"], MARGIN_CHOICES),
                "Density": _report_code(answers["density"], DENSITY_CHOICES),
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
