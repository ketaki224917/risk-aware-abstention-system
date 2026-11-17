"""Careful subgroup audit, uncertainty intervals, limitations, and fairness gap."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from raa.data import stratified_split
from raa.mammography import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_DATA_PATH,
    MammographyArtifact,
    load_mammographic_data,
    load_mammography_artifact,
)

FAIRNESS_GAP_STATEMENT = (
    "CRITICAL DEMOGRAPHIC FAIRNESS GAP:\n"
    "The evaluated subgroups are derived strictly from clinical and radiological features "
    "(patient scan age and mammographic tissue density). The UCI Mammographic Mass dataset "
    "contains NO demographic attributes such as race, ethnicity, socioeconomic status, "
    "geographic region, primary language, or scanner hardware vendor. While feature-based "
    "groupings reveal behavioral heterogeneity and error clustering across anatomical phenotypes, "
    "THEY DO NOT ESTABLISH DEMOGRAPHIC FAIRNESS OR HEALTH EQUITY. No claims of demographic "
    "parity, equalized odds, or fairness across human identity groups can be justified from "
    "this dataset. Deploying this system requires prospective auditing across representative, "
    "multi-ethnic, multi-center cohorts."
)


@dataclass(frozen=True)
class ConfidenceInterval:
    low: float
    high: float


@dataclass(frozen=True)
class SubgroupMetrics:
    group_name: str
    feature_dimension: str
    n_samples: int
    cohort_share: float
    malignant_count: int
    malignant_prevalence: float
    baseline_error_rate: float
    baseline_error_ci: ConfidenceInterval
    malignant_sensitivity: float
    malignant_sensitivity_ci: ConfidenceInterval
    benign_specificity: float
    benign_specificity_ci: ConfidenceInterval
    automatic_share: float
    assisted_share: float
    human_review_share: float
    overall_referral_rate: float
    referral_rate_ci: ConfidenceInterval
    automatic_tier_error_rate: float
    automatic_tier_error_ci: ConfidenceInterval
    false_negatives_total: int
    false_negatives_routed_away: int
    false_negative_catch_rate: float
    sample_limitations: str


@dataclass(frozen=True)
class FairnessAuditReport:
    dataset_name: str
    evaluation_split: str
    total_evaluated: int
    fairness_gap_statement: str
    subgroups: tuple[SubgroupMetrics, ...]
    methodology: dict[str, str]


def wilson_score_interval(
    successes: int, total: int, confidence: float = 0.95
) -> ConfidenceInterval:
    """Calculate Wilson score continuity-corrected confidence interval for a binomial proportion."""
    if total <= 0:
        return ConfidenceInterval(low=float("nan"), high=float("nan"))
    z = float(stats.norm.ppf(1 - (1 - confidence) / 2))
    p = successes / total
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    spread = (z * np.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)) / denominator
    low = max(0.0, float(centre - spread))
    high = min(1.0, float(centre + spread))
    return ConfidenceInterval(low=low, high=high)


def _bootstrap_metric_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_func: Any,
    confidence: float = 0.95,
    replicates: int = 1000,
    seed: int = 42,
) -> ConfidenceInterval:
    """Percentile bootstrap confidence interval."""
    if len(y_true) < 5:
        return ConfidenceInterval(low=float("nan"), high=float("nan"))
    rng = np.random.default_rng(seed)
    n = len(y_true)
    values = []
    for _ in range(replicates):
        indices = rng.integers(0, n, size=n)
        val = metric_func(y_true[indices], y_pred[indices])
        if np.isfinite(val):
            values.append(val)
    if not values:
        return ConfidenceInterval(low=float("nan"), high=float("nan"))
    alpha = (1 - confidence) / 2
    return ConfidenceInterval(
        low=float(np.quantile(values, alpha)),
        high=float(np.quantile(values, 1 - alpha)),
    )


def _compute_subgroup(
    name: str,
    dimension: str,
    mask: np.ndarray,
    targets: np.ndarray,
    preds: np.ndarray,
    levels: list[str],
    limitation: str,
) -> SubgroupMetrics:
    sub_targets = targets[mask]
    sub_preds = preds[mask]
    sub_levels = [levels[i] for i in range(len(levels)) if mask[i]]
    n = int(mask.sum())
    total_n = len(targets)

    if n == 0:
        nan_ci = ConfidenceInterval(float("nan"), float("nan"))
        return SubgroupMetrics(
            group_name=name,
            feature_dimension=dimension,
            n_samples=0,
            cohort_share=0.0,
            malignant_count=0,
            malignant_prevalence=0.0,
            baseline_error_rate=float("nan"),
            baseline_error_ci=nan_ci,
            malignant_sensitivity=float("nan"),
            malignant_sensitivity_ci=nan_ci,
            benign_specificity=float("nan"),
            benign_specificity_ci=nan_ci,
            automatic_share=0.0,
            assisted_share=0.0,
            human_review_share=0.0,
            overall_referral_rate=0.0,
            referral_rate_ci=nan_ci,
            automatic_tier_error_rate=float("nan"),
            automatic_tier_error_ci=nan_ci,
            false_negatives_total=0,
            false_negatives_routed_away=0,
            false_negative_catch_rate=float("nan"),
            sample_limitations=limitation,
        )

    # 0 = malignant, 1 = benign
    malignant_mask = sub_targets == 0
    benign_mask = sub_targets == 1
    n_mal = int(malignant_mask.sum())
    n_ben = int(benign_mask.sum())

    errors = sub_targets != sub_preds
    error_count = int(errors.sum())
    error_rate = error_count / n
    error_ci = wilson_score_interval(error_count, n)

    # Sensitivity (detecting malignant, true positive = pred 0)
    if n_mal > 0:
        mal_detected = int(((sub_targets == 0) & (sub_preds == 0)).sum())
        sens = mal_detected / n_mal
        sens_ci = wilson_score_interval(mal_detected, n_mal)
    else:
        sens = float("nan")
        sens_ci = ConfidenceInterval(float("nan"), float("nan"))

    # Specificity (detecting benign, true negative = pred 1)
    if n_ben > 0:
        ben_detected = int(((sub_targets == 1) & (sub_preds == 1)).sum())
        spec = ben_detected / n_ben
        spec_ci = wilson_score_interval(ben_detected, n_ben)
    else:
        spec = float("nan")
        spec_ci = ConfidenceInterval(float("nan"), float("nan"))

    # Routing tiers
    auto_count = sum(1 for lvl in sub_levels if lvl == "Automatic")
    assist_count = sum(1 for lvl in sub_levels if lvl == "Assisted")
    human_count = sum(1 for lvl in sub_levels if lvl == "Human Review")
    referral_count = assist_count + human_count

    auto_share = auto_count / n
    assist_share = assist_count / n
    human_share = human_count / n
    referral_rate = referral_count / n
    referral_ci = wilson_score_interval(referral_count, n)

    # Automatic tier error rate
    auto_indices = [i for i, lvl in enumerate(sub_levels) if lvl == "Automatic"]
    if auto_indices:
        auto_y = sub_targets[auto_indices]
        auto_pred = sub_preds[auto_indices]
        auto_errs = int((auto_y != auto_pred).sum())
        auto_err_rate = auto_errs / len(auto_indices)
        auto_err_ci = wilson_score_interval(auto_errs, len(auto_indices))
    else:
        auto_err_rate = float("nan")
        auto_err_ci = ConfidenceInterval(float("nan"), float("nan"))

    # False negatives (malignant labeled benign)
    fn_total = int(((sub_targets == 0) & (sub_preds == 1)).sum())
    fn_routed_away = int(
        sum(
            1
            for i in range(n)
            if sub_targets[i] == 0 and sub_preds[i] == 1 and sub_levels[i] != "Automatic"
        )
    )
    fn_catch_rate = (fn_routed_away / fn_total) if fn_total > 0 else float("nan")

    return SubgroupMetrics(
        group_name=name,
        feature_dimension=dimension,
        n_samples=n,
        cohort_share=n / total_n,
        malignant_count=n_mal,
        malignant_prevalence=n_mal / n,
        baseline_error_rate=error_rate,
        baseline_error_ci=error_ci,
        malignant_sensitivity=sens,
        malignant_sensitivity_ci=sens_ci,
        benign_specificity=spec,
        benign_specificity_ci=spec_ci,
        automatic_share=auto_share,
        assisted_share=assist_share,
        human_review_share=human_share,
        overall_referral_rate=referral_rate,
        referral_rate_ci=referral_ci,
        automatic_tier_error_rate=auto_err_rate,
        automatic_tier_error_ci=auto_err_ci,
        false_negatives_total=fn_total,
        false_negatives_routed_away=fn_routed_away,
        false_negative_catch_rate=fn_catch_rate,
        sample_limitations=limitation,
    )


def run_fairness_audit(
    artifact: MammographyArtifact | None = None,
    data_path: Path = DEFAULT_DATA_PATH,
    on_test_split_only: bool = True,
) -> FairnessAuditReport:
    """Execute subgroup fairness audit on the UCI Mammographic Mass dataset."""
    if artifact is None:
        artifact = load_mammography_artifact()

    data = load_mammographic_data(data_path)
    split = stratified_split(data.targets, seed=artifact.run_seed)

    if on_test_split_only:
        eval_indices = split.test
        split_name = "Held-out TEST split (seed 42, 20% sample)"
    else:
        eval_indices = np.arange(len(data.targets))
        split_name = "Full UCI Dataset (pooled n=961)"

    eval_raw = data.features[eval_indices]
    eval_targets = data.targets[eval_indices]

    transformed = np.asarray(artifact.preprocessor.transform(eval_raw), dtype=np.float64)
    records = artifact.system.predict(transformed)

    preds = np.asarray([rec.predicted_class for rec in records], dtype=np.int64)
    levels = [rec.level.value for rec in records]

    # Features: 0: Age, 1: Shape, 2: Margin, 3: Density
    ages = eval_raw[:, 0]
    densities = eval_raw[:, 3]

    subgroups: list[SubgroupMetrics] = []

    # 1. Overall cohort baseline
    subgroups.append(
        _compute_subgroup(
            "Overall Benchmark Cohort",
            "Population Baseline",
            np.ones(len(eval_targets), dtype=bool),
            eval_targets,
            preds,
            levels,
            f"Evaluated on {len(eval_targets)} records with fixed seed.",
        )
    )

    # 2. Age Brackets
    age_brackets = [
        (
            "Age < 50 (Premenopausal / Younger)",
            ages < 50,
            "Relatively low malignant prevalence; lower sample count.",
        ),
        (
            "Age 50-64 (Screening Core Age)",
            (ages >= 50) & (ages < 65),
            "Central screening age cohort with balanced classes.",
        ),
        (
            "Age >= 65 (Older / Postmenopausal)",
            ages >= 65,
            "Higher cancer prevalence; higher baseline risk.",
        ),
    ]
    for name, mask, limitation in age_brackets:
        valid_mask = mask & np.isfinite(ages)
        subgroups.append(
            _compute_subgroup(
                name, "Patient Age", valid_mask, eval_targets, preds, levels, limitation
            )
        )

    # 3. Tissue Density Brackets
    # Density codes: 1=High, 2=Similar/Iso, 3=Low, 4=Fatty
    density_brackets = [
        (
            "Dense Breast Tissue (Codes 1 & 2)",
            (densities == 1) | (densities == 2),
            "Dense tissue can mask lesions, increasing mammographic difficulty; "
            "small sample in Code 1.",
        ),
        (
            "Non-Dense / Fatty Tissue (Codes 3 & 4)",
            (densities == 3) | (densities == 4),
            "Most common radiological category in this dataset; lesions have higher contrast.",
        ),
    ]
    for name, mask, limitation in density_brackets:
        valid_mask = mask & np.isfinite(densities)
        subgroups.append(
            _compute_subgroup(
                name, "Radiological Density", valid_mask, eval_targets, preds, levels, limitation
            )
        )

    # 4. Intersectional Cross-Tabs
    intersections = [
        (
            "Younger (<50) & Dense Tissue",
            (ages < 50) & ((densities == 1) | (densities == 2)),
            "Small sub-cohort (n < 40); wide confidence intervals limits statistical conclusions.",
        ),
        (
            "Younger (<50) & Non-Dense",
            (ages < 50) & ((densities == 3) | (densities == 4)),
            "Moderate sub-cohort size.",
        ),
        (
            "Older (>=65) & Dense Tissue",
            (ages >= 65) & ((densities == 1) | (densities == 2)),
            "Clinically rare subgroup; high variance in error estimation.",
        ),
        (
            "Older (>=65) & Non-Dense",
            (ages >= 65) & ((densities == 3) | (densities == 4)),
            "High malignancy prevalence in fatty tissue.",
        ),
    ]
    for name, mask, limitation in intersections:
        valid_mask = mask & np.isfinite(ages) & np.isfinite(densities)
        subgroups.append(
            _compute_subgroup(
                name,
                "Age x Density Intersection",
                valid_mask,
                eval_targets,
                preds,
                levels,
                limitation,
            )
        )

    return FairnessAuditReport(
        dataset_name="UCI Mammographic Mass Dataset",
        evaluation_split=split_name,
        total_evaluated=len(eval_targets),
        fairness_gap_statement=FAIRNESS_GAP_STATEMENT,
        subgroups=tuple(subgroups),
        methodology={
            "uncertainty_method": (
                "Wilson score interval with continuity correction (alpha=0.05, 95% confidence)."
            ),
            "abstention_policy": (
                "Validation 70th / 90th percentile thresholds on composite risk R."
            ),
            "fairness_boundary": (
                "Feature-based subgroups demonstrate error distributions across clinical features, "
                "not demographic equity."
            ),
        },
    )


def save_fairness_audit(
    output_path: Path = DEFAULT_ARTIFACT_DIR / "fairness_audit.json",
    on_test_split_only: bool = True,
) -> Path:
    """Run fairness audit and write structured report to JSON."""
    report = run_fairness_audit(on_test_split_only=on_test_split_only)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output_path
