"""Interactive local demo of the three-level research routing policy."""

from __future__ import annotations

import streamlit as st

from raa.config import load_config
from raa.data import load_breast_cancer_data, stratified_split
from raa.explain.checker import check_explanation
from raa.explain.templates import generate_explanation
from raa.pipeline import DecisionSystem, fit_system

st.set_page_config(page_title="Risk-Aware Abstention", page_icon="🧭", layout="centered")
st.title("Risk-Aware Abstention")
st.warning("Research prototype only. Not clinically validated and not for real diagnosis.")
st.caption(
    "This demo illustrates a methodological prototype on Wisconsin Diagnostic Breast Cancer data."
)


@st.cache_resource
def load_demo() -> tuple[object, DecisionSystem, object]:
    """Train once on a fixed train/validation split; keep the test partition held out."""
    config = load_config()
    data = load_breast_cancer_data()
    split = stratified_split(data.targets, seed=int(config["data"]["base_seed"]))
    system = fit_system(
        data.features,
        data.targets,
        split.train,
        split.validation,
        config,
        seed=int(config["data"]["base_seed"]),
    )
    return data, system, split


with st.spinner("Training the reproducible demo models on the training split…"):
    data, system, split = load_demo()

row = st.selectbox(
    "Choose a held-out test example",
    range(len(split.test)),
    format_func=lambda value: f"Test example {value + 1}",
)
record = system.predict(data.features[split.test[row : row + 1]])[0]
explanation = generate_explanation(record)
check = check_explanation(record, explanation)

color = {"Automatic": "green", "Assisted": "orange", "Human Review": "red"}[record.level.value]
st.markdown(f"### Decision: :{color}[{record.level.value}]")
left, right = st.columns(2)
left.metric("Predicted class", record.predicted_label)
right.metric("Malignant probability", f"{record.malignant_probability:.1%}")
st.subheader("Decision record")
st.json(
    {
        "uncertainty_signal_normalized": round(record.uncertainty, 4),
        "anomaly_score_normalized": round(record.anomaly, 4),
        "consequence_design_value": round(record.consequence, 4),
        "risk": round(record.risk, 4),
        "automatic_threshold_t70": round(record.automatic_threshold, 4),
        "assisted_threshold_t90": round(record.assisted_threshold, 4),
    }
)
st.subheader("Grounded explanation")
st.write(explanation)
if check.passed:
    st.success("Rule-based explanation checks passed.")
else:
    st.error("Explanation checker found: " + ", ".join(check.issues))
st.caption(
    "Ensemble disagreement is an uncertainty signal, not a calibrated probability of error. "
    "Risk weights and consequence values are design assumptions. The explanation layer "
    "does not alter prediction or routing."
)
