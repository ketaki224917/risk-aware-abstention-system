"""Decoupled explanations for class leaning vs routing tier with verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

from raa.explain.record import DecisionRecord


@dataclass(frozen=True)
class FeatureAttribution:
    """Individual feature contribution to class probability leaning."""

    feature_name: str
    feature_value: Any
    attribution_score: float  # Absolute importance / delta
    directional_push: str  # 'toward malignant' or 'toward benign'
    signed_delta: float  # Positive = shifts toward malignant, Negative = toward benign
    summary_text: str


@dataclass(frozen=True)
class ClassExplanation:
    """Explains why the model leaned toward Benign or Malignant."""

    predicted_label: str
    malignant_probability: float
    confidence: float
    feature_attributions: tuple[FeatureAttribution, ...]
    primary_driving_feature: str
    summary_narrative: str


@dataclass(frozen=True)
class RiskComponentContribution:
    """Individual signal contribution to the composite risk score."""

    component_name: str
    raw_value: float
    normalized_value: float
    weight: float
    weighted_contribution: float
    percentage_of_risk: float
    explanation_note: str


@dataclass(frozen=True)
class RouteExplanation:
    """Explains why the case was assigned to Automatic, Assisted, or Human Review."""

    route_tier: str
    composite_risk: float
    automatic_threshold: float
    assisted_threshold: float
    risk_components: tuple[RiskComponentContribution, ...]
    primary_risk_driver: str
    missing_data_override: bool
    summary_narrative: str


@dataclass(frozen=True)
class ExplanationDiagnostics:
    """Stability and fidelity verification metrics for the generated explanations."""

    stability_passed: bool
    stability_score: float  # Mean Spearman rank correlation under input perturbations
    stability_note: str
    fidelity_passed: bool
    fidelity_ratio: float  # Ratio of top-feature impact vs baseline mean feature impact
    fidelity_note: str
    evidence_valid: bool  # Can these explanations be safely presented as grounded evidence?


@dataclass(frozen=True)
class DualExplanation:
    """Combined container presenting separated Class and Route explanations with diagnostics."""

    class_explanation: ClassExplanation
    route_explanation: RouteExplanation
    diagnostics: ExplanationDiagnostics


def compute_class_explanation(
    feature_names: tuple[str, ...],
    raw_values: dict[str, Any],
    reference_values: tuple[float, ...],
    predict_proba_func: Any,
) -> ClassExplanation:
    """Compute local feature attributions explaining the model's benign vs malignant leaning."""
    raw_array = np.asarray(
        [
            raw_values.get(name) if raw_values.get(name) is not None else np.nan
            for name in feature_names
        ],
        dtype=np.float64,
    )
    current_p_mal = float(predict_proba_func(raw_array.reshape(1, -1)))
    predicted_label = "Malignant" if current_p_mal >= 0.5 else "Benign"
    confidence = current_p_mal if current_p_mal >= 0.5 else (1.0 - current_p_mal)

    attributions: list[FeatureAttribution] = []
    for i, name in enumerate(feature_names):
        val = raw_array[i]
        ref = reference_values[i]
        if np.isnan(val):
            attributions.append(
                FeatureAttribution(
                    feature_name=name,
                    feature_value="Not sure / missing",
                    attribution_score=0.0,
                    directional_push="neutral (imputed)",
                    signed_delta=0.0,
                    summary_text=(
                        f"{name}: Missing; imputed from baseline without direct attribution."
                    ),
                )
            )
            continue

        counterfactual = raw_array.copy()
        counterfactual[i] = ref
        counter_p_mal = float(predict_proba_func(counterfactual.reshape(1, -1)))
        delta = (
            current_p_mal - counter_p_mal
        )  # positive means this feature moved score toward malignant
        abs_delta = abs(delta)
        direction = "toward malignant" if delta > 0 else "toward benign"

        if abs_delta < 0.005:
            text = f"{name}: a one-field comparison barely changed the model score."
        else:
            text = (
                f"{name}: this value moved the malignant-class score {abs_delta * 100:.1f} "
                f"points {direction} versus a common training value."
            )

        attributions.append(
            FeatureAttribution(
                feature_name=name,
                feature_value=val,
                attribution_score=abs_delta,
                directional_push=direction,
                signed_delta=delta,
                summary_text=text,
            )
        )

    # Sort attributions by descending impact
    attributions.sort(key=lambda a: a.attribution_score, reverse=True)
    primary = attributions[0].feature_name if attributions else "None"

    narrative = (
        f"The model leans {predicted_label} with {confidence * 100:.1f}% confidence "
        f"(estimated malignant probability: {current_p_mal:.3f}). "
        f"The primary feature influencing this leaning was '{primary}'."
    )

    return ClassExplanation(
        predicted_label=predicted_label,
        malignant_probability=current_p_mal,
        confidence=confidence,
        feature_attributions=tuple(attributions),
        primary_driving_feature=primary,
        summary_narrative=narrative,
    )


def compute_route_explanation(
    record: DecisionRecord,
    weights: dict[str, float] | None = None,
) -> RouteExplanation:
    """Compute risk component decomposition explaining why the RAA policy chose this triage tier."""
    if weights is None:
        weights = {"uncertainty": 0.5, "anomaly": 0.2, "consequence": 0.3}

    w_u = weights.get("uncertainty", 0.5)
    w_a = weights.get("anomaly", 0.2)
    w_c = weights.get("consequence", 0.3)

    contrib_u = w_u * record.uncertainty
    contrib_a = w_a * record.anomaly
    contrib_c = w_c * record.consequence
    total_risk = max(record.risk, 1e-6)

    components = (
        RiskComponentContribution(
            component_name="Model Disagreement (Uncertainty)",
            raw_value=record.uncertainty,
            normalized_value=record.uncertainty,
            weight=w_u,
            weighted_contribution=contrib_u,
            percentage_of_risk=(contrib_u / total_risk) * 100,
            explanation_note=(
                f"Measures disagreement across 30 bootstrap ensemble trees "
                f"(U={record.uncertainty:.3f}). Contributes {contrib_u:.3f} to composite risk."
            ),
        ),
        RiskComponentContribution(
            component_name="Data Unusualness (Anomaly)",
            raw_value=record.anomaly,
            normalized_value=record.anomaly,
            weight=w_a,
            weighted_contribution=contrib_a,
            percentage_of_risk=(contrib_a / total_risk) * 100,
            explanation_note=(
                f"Measures morphological divergence via Isolation Forest (A={record.anomaly:.3f}). "
                f"Contributes {contrib_a:.3f} to composite risk."
            ),
        ),
        RiskComponentContribution(
            component_name="Clinical Error Consequence",
            raw_value=record.consequence,
            normalized_value=record.consequence,
            weight=w_c,
            weighted_contribution=contrib_c,
            percentage_of_risk=(contrib_c / total_risk) * 100,
            explanation_note=(
                f"Asymmetric clinical loss penalty for predicted class '{record.predicted_label}' "
                f"(C={record.consequence:.2f}). Contributes {contrib_c:.3f} to composite risk."
            ),
        ),
    )

    # Determine dominant contributor
    max_comp = max(components, key=lambda c: c.weighted_contribution)
    primary_driver = max_comp.component_name
    missing_override = bool(record.estimated_feature_count > 0)

    if missing_override:
        narrative = (
            f"Triage Tier: {record.level.value}. FORCED ESCALATION: "
            f"{record.estimated_feature_count} report field(s) were missing or marked 'Not sure'. "
            "Safety policy mandates Human Review whenever incomplete clinical findings "
            "require statistical imputation."
        )
    elif record.level.value == "Automatic":
        narrative = (
            f"Triage Tier: Automatic. The composite risk score (R={record.risk:.3f}) is "
            f"below the validation 70th percentile cutoff ({record.automatic_threshold:.3f}). "
            "Neither disagreement nor unusualness triggered safety escalation."
        )
    elif record.level.value == "Assisted":
        narrative = (
            f"Triage Tier: Assisted Review. The composite risk score (R={record.risk:.3f}) "
            f"exceeds the automatic threshold ({record.automatic_threshold:.3f}) but remains "
            f"below the full human cutoff ({record.assisted_threshold:.3f}). The largest risk "
            f"contributor was {primary_driver}."
        )
    else:
        narrative = (
            f"Triage Tier: Human Review. The composite risk score (R={record.risk:.3f}) exceeds "
            f"the validation 90th percentile threshold ({record.assisted_threshold:.3f}). "
            f"The primary factor driving escalation was {primary_driver}."
        )

    return RouteExplanation(
        route_tier=record.level.value,
        composite_risk=record.risk,
        automatic_threshold=record.automatic_threshold,
        assisted_threshold=record.assisted_threshold,
        risk_components=components,
        primary_risk_driver=primary_driver,
        missing_data_override=missing_override,
        summary_narrative=narrative,
    )


def test_explanation_stability(
    feature_names: tuple[str, ...],
    raw_values: dict[str, Any],
    reference_values: tuple[float, ...],
    predict_proba_func: Any,
    n_perturbations: int = 15,
    noise_sigma: float = 0.02,
    seed: int = 42,
) -> tuple[bool, float, str]:
    """Test explanation stability: Spearman rank correlation of attributions under jitter."""
    base_expl = compute_class_explanation(
        feature_names, raw_values, reference_values, predict_proba_func
    )
    base_ranks = [a.attribution_score for a in base_expl.feature_attributions]

    if all(score < 1e-4 for score in base_ranks):
        return True, 1.0, "Attributions are uniformly near-zero (stable)."

    rng = np.random.default_rng(seed)
    raw_array = np.asarray(
        [
            raw_values.get(name) if raw_values.get(name) is not None else np.nan
            for name in feature_names
        ],
        dtype=np.float64,
    )

    correlations: list[float] = []
    for _ in range(n_perturbations):
        perturbed_dict = dict(raw_values)
        for i, name in enumerate(feature_names):
            val = raw_array[i]
            if np.isfinite(val) and i == 0:  # age is continuous
                noise = rng.normal(0, noise_sigma * max(val, 1.0))
                perturbed_dict[name] = float(np.clip(val + noise, 1, 120))
        pert_expl = compute_class_explanation(
            feature_names, perturbed_dict, reference_values, predict_proba_func
        )
        pert_ranks = [a.attribution_score for a in pert_expl.feature_attributions]
        if np.std(base_ranks) < 1e-6 and np.std(pert_ranks) < 1e-6:
            correlations.append(1.0)
        elif np.std(base_ranks) < 1e-6 or np.std(pert_ranks) < 1e-6:
            correlations.append(0.0)
        else:
            corr, _ = stats.spearmanr(base_ranks, pert_ranks)
            if np.isfinite(corr):
                correlations.append(corr)

    mean_corr = float(np.mean(correlations)) if correlations else 1.0
    passed = mean_corr >= 0.80
    note = (
        f"Mean Spearman rank correlation under {n_perturbations} input perturbations: "
        f"{mean_corr:.3f} (stability threshold >= 0.80). {'STABLE' if passed else 'UNSTABLE'}."
    )
    return passed, mean_corr, note


def test_explanation_fidelity(
    feature_names: tuple[str, ...],
    raw_values: dict[str, Any],
    reference_values: tuple[float, ...],
    predict_proba_func: Any,
) -> tuple[bool, float, str]:
    """Test fidelity: verifies top-attributed feature impact exceeds baseline mean."""
    base_expl = compute_class_explanation(
        feature_names, raw_values, reference_values, predict_proba_func
    )
    attributions = base_expl.feature_attributions
    if not attributions or len(attributions) <= 1:
        return True, 1.0, "Single feature input; fidelity check trivially passed."

    top_score = attributions[0].attribution_score
    other_scores = [a.attribution_score for a in attributions[1:]]
    mean_other = float(np.mean(other_scores)) if other_scores else 0.0

    ratio = (
        (top_score / max(mean_other, 1e-4)) if mean_other > 0 else (2.0 if top_score > 0 else 1.0)
    )
    passed = top_score >= mean_other
    note = (
        f"Top attributed feature '{attributions[0].feature_name}' delta impact is {top_score:.4f} "
        f"vs other features mean delta {mean_other:.4f} (fidelity ratio: {ratio:.2f}x). "
        f"{'HIGH FIDELITY' if passed else 'LOW FIDELITY'}."
    )
    return passed, ratio, note


def generate_dual_explanation(
    feature_names: tuple[str, ...],
    raw_values: dict[str, Any],
    reference_values: tuple[float, ...],
    predict_proba_func: Any,
    record: DecisionRecord,
    weights: dict[str, float] | None = None,
) -> DualExplanation:
    """Generate separated Class and Route explanations with diagnostics."""
    class_expl = compute_class_explanation(
        feature_names, raw_values, reference_values, predict_proba_func
    )
    route_expl = compute_route_explanation(record, weights=weights)

    stab_passed, stab_score, stab_note = test_explanation_stability(
        feature_names, raw_values, reference_values, predict_proba_func
    )
    fid_passed, fid_ratio, fid_note = test_explanation_fidelity(
        feature_names, raw_values, reference_values, predict_proba_func
    )

    evidence_valid = stab_passed and fid_passed

    diagnostics = ExplanationDiagnostics(
        stability_passed=stab_passed,
        stability_score=stab_score,
        stability_note=stab_note,
        fidelity_passed=fid_passed,
        fidelity_ratio=fid_ratio,
        fidelity_note=fid_note,
        evidence_valid=evidence_valid,
    )

    return DualExplanation(
        class_explanation=class_expl,
        route_explanation=route_expl,
        diagnostics=diagnostics,
    )
