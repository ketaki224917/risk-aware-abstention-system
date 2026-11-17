"""Simple report-entry interface backed by the saved UCI mammography RAA model."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import streamlit as st

from raa.agent_ethics import get_agent_architecture, get_ethics_perspectives, get_task_environment
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
from raa.eval.fairness_audit import FAIRNESS_GAP_STATEMENT, run_fairness_audit
from raa.eval.workload_simulation import HUMAN_REVIEW_CLAIM_BOUNDARY, run_workload_simulation
from raa.explain.llm_adapter import LLMUnavailableError, generate_prediction_narrative
from raa.governance import get_lifecycle_governance, get_model_card_mammography, get_risk_register
from raa.mammography import (
    DEFAULT_ARTIFACT_DIR,
    MammographyArtifact,
    explain_mammography_case,
    explain_mammography_case_dual,
    load_mammography_artifact,
    predict_mammography_case,
)
from raa.risk.policy import DecisionLevel

APP_TITLE = "Risk Aware Abstention System"


@st.cache_data
def _load_evaluation() -> dict[str, Any]:
    return json.loads((DEFAULT_ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))


@st.cache_data
def _load_fairness_report() -> Any:
    return run_fairness_audit(on_test_split_only=True)


@st.cache_data
def _load_workload_report() -> Any:
    return run_workload_simulation()


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
            dual_explanation=submission.get("dual_explanation"),
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


def _render_agent_and_ethics() -> None:
    """Render the syllabus-aligned utility agent and ethics analysis."""
    with st.expander("Syllabus-Aligned Agent & Ethics Analysis"):
        st.markdown("### Utility-Based Decision Agent Specification")
        arch = get_agent_architecture()
        env = get_task_environment()
        st.write(
            f"**Agent Taxonomy:** `{arch.agent_type}`. Rather than maximizing raw accuracy, "
            "the agent optimizes an explicit clinical utility function balancing false negative "
            "harm against clinical human review capacity."
        )
        st.markdown(
            "**Formal Decision Policy:** "
            r"$\pi(\mathbf{x}) = \text{Automatic if } R \le t_{70} \text{ else } "
            r"(\text{Assisted if } R \le t_{90} \text{ else Human Review})$"
        )
        st.caption(env.performance_measure)

        st.markdown("#### PEAS Task Environment")
        st.table(
            [
                {
                    "PEAS Dimension": "Performance Measure",
                    "Specification": env.performance_measure[:100] + "...",
                },
                {"PEAS Dimension": "Environment", "Specification": env.environment[:100] + "..."},
                {"PEAS Dimension": "Actuators", "Specification": env.actuators},
                {"PEAS Dimension": "Sensors", "Specification": env.sensors},
            ]
        )

        st.markdown("#### Tripartite Ethics Evaluation")
        ethics = get_ethics_perspectives()
        cols = st.columns(3)
        for col, key in zip(cols, ("utilitarian", "deontological", "virtue_ethics"), strict=True):
            pers = ethics[key]
            with col, st.container(border=True):
                st.markdown(f"**{pers.framework_name}**")
                st.caption(f"*Core Principle:* {pers.core_principle}")
                st.write(pers.agent_manifestation)
                st.info(f"**Trade-off:** {pers.concrete_tradeoff}")


def _render_governance_section() -> None:
    """Render the AI Impact Assessment, Risk Register, and Model Card highlights."""
    with st.expander("AI Impact Assessment & Risk Register"):
        st.markdown("### Concise AI Safety Risk Register")
        register = get_risk_register()
        reg_rows = [
            {
                "ID": item.risk_id,
                "Foreseeable Harm": item.foreseeable_harm[:80] + "...",
                "Severity": item.pre_mitigation_severity,
                "Key Mitigation": item.mitigations[0],
                "Owner": item.responsible_owner.split("&")[0].strip(),
                "Residual Risk": item.residual_risk[:35] + "...",
            }
            for item in register
        ]
        st.table(reg_rows)

        st.markdown("### Model Card & Datasheet Summary")
        card = get_model_card_mammography()
        gov = get_lifecycle_governance()
        st.write(f"**Model Name:** {card.model_name} (v{card.model_version})")
        st.write(f"**Intended Use:** {card.intended_use}")
        st.write(f"**Out-of-Scope:** {card.out_of_scope_uses}")
        st.caption(f"Governance Privacy: {gov['privacy_and_security']['network_isolation']}")


def _render_fairness_section() -> None:
    """Render the subgroup fairness audit and explicit demographic fairness gap."""
    with st.expander("Subgroup Fairness Audit & Demographic Gap"):
        st.error(FAIRNESS_GAP_STATEMENT)
        report = _load_fairness_report()
        st.write(
            f"Evaluated on {report.total_evaluated} held-out cases with "
            "Wilson 95% Confidence Intervals."
        )
        table_rows = []
        for sub in report.subgroups[:6]:
            elo, ehi = sub.baseline_error_ci.low, sub.baseline_error_ci.high
            err_ci = f"{sub.baseline_error_rate:.1%} [{elo:.1%}-{ehi:.1%}]"
            slo, shi = sub.malignant_sensitivity_ci.low, sub.malignant_sensitivity_ci.high
            sens_ci = (
                f"{sub.malignant_sensitivity:.1%} [{slo:.1%}-{shi:.1%}]"
                if not np.isnan(sub.malignant_sensitivity)
                else "N/A"
            )
            table_rows.append(
                {
                    "Subgroup": sub.group_name,
                    "N": sub.n_samples,
                    "Malignant Prev": f"{sub.malignant_prevalence:.1%}",
                    "Error Rate [95% CI]": err_ci,
                    "Sensitivity [95% CI]": sens_ci,
                    "FN Catch Rate": f"{sub.false_negative_catch_rate:.1%}"
                    if not np.isnan(sub.false_negative_catch_rate)
                    else "N/A",
                }
            )
        st.table(table_rows)
        st.caption(
            "Notice: In younger patients (<50), malignant prevalence is lower and raw sensitivity "
            "drops, but RAA abstention catches ~67% of missed malignancies and routes them "
            "for human verification."
        )


def _render_workload_section() -> None:
    """Render the human review workload capacity sweep and offline simulation."""
    with st.expander("Human Review Workload & Capacity Simulation"):
        st.warning(HUMAN_REVIEW_CLAIM_BOUNDARY)
        sim = _load_workload_report()
        st.markdown("### Validation Capacity Sweep (Cases Reviewed per 100)")
        sweep_rows = []
        for row in sim.capacity_sweep:
            sweep_rows.append(
                {
                    "Capacity Budget": f"{row.capacity_per_100:.0f}%",
                    "Percentiles": (
                        f"p{row.automatic_percentile:.0f} / p{row.assisted_percentile:.1f}"
                    ),
                    "Automatic Cases": f"{row.automatic_count} ({row.automatic_share:.1%})",
                    "Assisted": f"{row.assisted_count} ({row.assisted_share:.1%})",
                    "Human Review": f"{row.human_review_count} ({row.human_review_share:.1%})",
                    "Auto Tier Error": f"{row.automatic_tier_error_rate:.1%}",
                    "FN Catch Rate": f"{row.false_negative_catch_rate:.1%}",
                }
            )
        st.table(sweep_rows)

        st.markdown("### Offline Review Policy Simulations")
        for pol in sim.offline_policy_simulations:
            st.markdown(f"**{pol.policy_name}**")
            st.write(
                f"• Reviewer model: *{pol.reviewer_model_assumed}* | "
                f"Net error rate: **{pol.net_system_error_rate:.1%}** | "
                f"Unreviewed false negatives: **{pol.unreviewed_false_negatives}** | "
                f"Workload: {pol.workload_case_count} cases"
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

    dual = submission.get("dual_explanation")
    st.subheader("Why the model leaned this way")
    if dual is not None:
        st.caption("Class Explanation - why the model leaned Benign or Malignant:")
        st.write(dual.class_explanation.summary_narrative)
        for attrib in dual.class_explanation.feature_attributions:
            st.write(f"- {attrib.summary_text}")
        with st.container(border=True):
            st.caption("Explanation Verification Diagnostics:")
            d_cols = st.columns(2)
            d_cols[0].write(
                f"• Stability: {'PASSED' if dual.diagnostics.stability_passed else 'FLAGGED'} "
                f"({dual.diagnostics.stability_note})"
            )
            d_cols[1].write(
                f"• Fidelity: {'PASSED' if dual.diagnostics.fidelity_passed else 'FLAGGED'} "
                f"({dual.diagnostics.fidelity_note})"
            )
    else:
        for explanation in submission["explanations"]:
            st.write(f"- {explanation}")

    with st.expander("How the RAA route was chosen"):
        if dual is not None:
            st.caption("Route Explanation - why this triage route was chosen:")
            st.write(dual.route_explanation.summary_narrative)
            st.markdown(
                f"**Primary risk contributor:** `{dual.route_explanation.primary_risk_driver}`"
            )

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

    # The 4 comprehensive academic and governance additions
    _render_agent_and_ethics()
    _render_governance_section()
    _render_fairness_section()
    _render_workload_section()

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
            dual_explanation = None
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
                dual_explanation = explain_mammography_case_dual(values, record, artifact)
            except ValueError as error:
                st.error(str(error))
                return

        st.session_state["health_submission"] = {
            "answers": answers,
            "record": record,
            "explanations": explanations,
            "dual_explanation": dual_explanation if status == REPORT_HAS_MASS else None,
        }

    submission = st.session_state.get("health_submission")
    if submission is not None and submission["answers"] == answers:
        st.divider()
        _render_prediction(submission)
