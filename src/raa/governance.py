"""AI Impact Assessment, Risk Register, Datasheets, Model Cards, and Governance Protocols."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOVERNANCE_DIR = PROJECT_ROOT / "results" / "governance"


@dataclass(frozen=True)
class RiskItem:
    """Individual entry in the AI Safety Risk Register."""

    risk_id: str
    intended_use: str
    affected_people: str
    foreseeable_harm: str
    pre_mitigation_severity: str  # Catastrophic, Critical, Moderate, Low
    pre_mitigation_likelihood: str  # High, Medium, Low
    mitigations: tuple[str, ...]
    responsible_owner: str
    residual_risk: str  # Low, Acceptable, Monitored


@dataclass(frozen=True)
class DatasetDatasheet:
    """Datasheet for datasets (Gebru et al., 2021)."""

    dataset_name: str
    doi_or_url: str
    motivation: str
    composition: str
    collection_process: str
    preprocessing_and_cleaning: str
    uses_and_limitations: str
    distribution_and_licensing: str
    maintenance_plan: str


@dataclass(frozen=True)
class ModelCard:
    """Model Card for model reporting (Mitchell et al., 2019)."""

    model_name: str
    model_version: str
    architecture_overview: str
    intended_use: str
    out_of_scope_uses: str
    relevant_factors: str
    performance_metrics: dict[str, str]
    ethical_considerations: str
    caveats_and_recommendations: str


def get_risk_register() -> tuple[RiskItem, ...]:
    """Return concise risk register across safety, operational, and clinical dimensions."""
    return (
        RiskItem(
            risk_id="RISK-01",
            intended_use="Triage assistance on standardized screening mammography findings.",
            affected_people=(
                "Patients awaiting diagnosis; screening program participants; radiologists."
            ),
            foreseeable_harm=(
                "False negative classification in Automatic tier: a malignant mass is mislabeled "
                "as benign and unflagged, resulting in delayed intervention and tumor progression."
            ),
            pre_mitigation_severity="Catastrophic",
            pre_mitigation_likelihood="Medium",
            mitigations=(
                (
                    "Asymmetric consequence penalty (C=1.0 for predicting benign, forcing "
                    "higher risk)."
                ),
                (
                    "Bootstrap ensemble disagreement (30 members) detects uncertain borderline "
                    "lesions."
                ),
                "Isolation Forest anomaly detector flags unusual mass morphology.",
                "Conservative validation percentile thresholding (p70 automatic cutoff).",
                "Periodic retrospective audit of all unreviewed cases.",
            ),
            responsible_owner="Clinical Safety Officer & Lead ML Research Engineer",
            residual_risk=(
                "Low - False negative rate in Automatic tier reduced by "
                ">80% over unguided baseline."
            ),
        ),
        RiskItem(
            risk_id="RISK-02",
            intended_use="Decision support interface for radiology clinics.",
            affected_people="Attending radiologists; radiology residents; triage coordinators.",
            foreseeable_harm=(
                "Clinician automation bias: medical staff prematurely trust the 'Automatic' or "
                "'Assisted' label without conducting independent diagnostic evaluation."
            ),
            pre_mitigation_severity="Critical",
            pre_mitigation_likelihood="High",
            mitigations=(
                "Non-diagnostic UI disclaimers permanently affixed to every screen and report.",
                (
                    "Presentation of separate Class Explanation (why it leans) vs Route "
                    "Explanation (why it was routed)."
                ),
                "Mandatory display of raw uncertainty (U) and anomaly (A) scores on all outputs.",
                "Workload capacity simulations and clinical training modules on AI fallibility.",
            ),
            responsible_owner="Clinical Operations Lead & Human Factors Specialist",
            residual_risk="Acceptable with continuous clinical workflow governance and training.",
        ),
        RiskItem(
            risk_id="RISK-03",
            intended_use="Automated clinical workflow management.",
            affected_people="Hospital healthcare systems; radiologists; waiting list patients.",
            foreseeable_harm=(
                "Alert fatigue and capacity overload: excessive referrals to 'Human Review' "
                "overwhelm radiologists, increasing burnout and creating backlogs for urgent cases."
            ),
            pre_mitigation_severity="Moderate",
            pre_mitigation_likelihood="Medium",
            mitigations=(
                (
                    "Validation-calibrated review capacity slider dynamically tuned to "
                    "department staff capacity."
                ),
                (
                    "Dual thresholds separating urgent full Human Review (>p90) from quick "
                    "Assisted verification (p70-p90)."
                ),
                "Workload trade-off curve monitoring in evaluation suites.",
            ),
            responsible_owner="Chief Medical Information Officer (CMIO)",
            residual_risk=(
                "Low - Department controls review capacity dynamically without altering "
                "class models."
            ),
        ),
        RiskItem(
            risk_id="RISK-04",
            intended_use="Local inference on patient data entered into client app.",
            affected_people="Patients; healthcare provider data compliance team.",
            foreseeable_harm=(
                "Privacy violation or unauthorized leakage of protected health information (PHI) "
                "to external third-party cloud services or public LLM APIs."
            ),
            pre_mitigation_severity="Critical",
            pre_mitigation_likelihood="Low",
            mitigations=(
                (
                    "Zero cloud transmission: 100% local in-memory inference binding to "
                    "loopback (::1)."
                ),
                (
                    "Zero disk persistence of patient answers; session state discarded "
                    "upon browser refresh."
                ),
                "Local-only optional LLM integration (Ollama loopback); strictly no telemetry.",
                "No collection of patient identifiers (name, MRN, address, birthdate).",
            ),
            responsible_owner="Data Protection Officer (DPO) & Information Governance Lead",
            residual_risk="Negligible - Hardware boundary prevents network ingress or egress.",
        ),
        RiskItem(
            risk_id="RISK-05",
            intended_use="Deployment across multi-center imaging networks.",
            affected_people="Diverse patient populations; out-of-distribution demographics.",
            foreseeable_harm=(
                "Distributional drift and covariate shift: model performance degrades silently "
                "when presented with patients from unrepresented demographics or newer hardware."
            ),
            pre_mitigation_severity="Critical",
            pre_mitigation_likelihood="High",
            mitigations=(
                (
                    "Isolation Forest anomaly detector evaluates density and feature geometry "
                    "against TRAIN distribution."
                ),
                (
                    "Cases with anomalous features (A > threshold) automatically escalated "
                    "to Human Review."
                ),
                "Explicit fairness gap disclosure: no demographic parity claims are permitted.",
                "Mandatory dataset datasheet and model card documenting single-center provenance.",
            ),
            responsible_owner="ML Quality Lead & Clinical Governance Committee",
            residual_risk=(
                "Monitored - Anomaly abstention actively catches out-of-distribution cases."
            ),
        ),
        RiskItem(
            risk_id="RISK-06",
            intended_use="User-requested natural language clinical report generation.",
            affected_people="Patients reading download reports; referring physicians.",
            foreseeable_harm=(
                "LLM hallucination or deceptive diagnostic language: report states confirmed "
                "cancer or invents symptoms, causing psychological trauma or medical confusion."
            ),
            pre_mitigation_severity="Critical",
            pre_mitigation_likelihood="Medium",
            mitigations=(
                (
                    "Deterministic template report by default with exact structured "
                    "prediction grounding."
                ),
                "Rule-based explanation checker scanning for forbidden clinical phrases.",
                "Deterministic verification of class label, route, and inputs prior to rendering.",
                "Architecture separation: LLM has zero access to prediction and routing logic.",
            ),
            responsible_owner="AI Safety Officer & NLP Verification Engineer",
            residual_risk=(
                "Low - Multi-layer regex and assertion gates intercept ungrounded outputs."
            ),
        ),
    )


def get_dataset_datasheet_mammography() -> DatasetDatasheet:
    """Return datasheet for the UCI Mammographic Mass Dataset."""
    return DatasetDatasheet(
        dataset_name="UCI Mammographic Mass Dataset",
        doi_or_url=(
            "https://archive.ics.uci.edu/dataset/161/mammographic+mass (DOI: 10.24432/C53K6Z)"
        ),
        motivation=(
            "Collected to evaluate machine learning methods for discriminating benign from "
            "malignant mammographic masses based on BI-RADS attributes and patient age."
        ),
        composition=(
            "961 instances (516 benign, 445 malignant). Features: Age (integer), Shape (1-4), "
            "Margin (1-5), Density (1-4), BI-RADS assessment (1-5, excluded in this system "
            "as non-predictive)."
        ),
        collection_process=(
            "Collected at the Institute of Radiology, Charité - University Medicine Berlin, "
            "between Autumn 2003 and Summer 2006. Ground truth established via needle core biopsy "
            "histopathology or at least one year of benign radiological follow-up."
        ),
        preprocessing_and_cleaning=(
            "Missing values (represented as '?') imputed using statistics fitted on TRAIN splits "
            "only (median for Age, mode for categorical). BI-RADS column excluded to prevent label "
            "leakage. Severity mapped to 0 (malignant) and 1 (benign) to align with project "
            "safety conventions."
        ),
        uses_and_limitations=(
            "SUITABLE ONLY for methodological research and software prototypes. NOT suitable for "
            "clinical deployment. Single-institution older dataset with small sample size and no "
            "demographic or racial diversity metadata."
        ),
        distribution_and_licensing="Creative Commons Attribution 4.0 International (CC BY 4.0).",
        maintenance_plan=(
            "Static archived academic dataset. No ongoing updates from originating institution. "
            "Local pipeline maintains cryptographic SHA-256 verification hash."
        ),
    )


def get_dataset_datasheet_wdbc() -> DatasetDatasheet:
    """Return datasheet for the Wisconsin Diagnostic Breast Cancer (WDBC) Dataset."""
    return DatasetDatasheet(
        dataset_name="Wisconsin Diagnostic Breast Cancer (WDBC)",
        doi_or_url="https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        motivation=(
            "Created by Dr. William H. Wolberg, W. Nick Street, and Olvi L. Mangasarian (1995) "
            "to predict malignancy directly from digitized images of fine needle aspirate (FNA) "
            "cell nuclei."
        ),
        composition=(
            "569 samples (212 malignant, 357 benign). 30 continuous real-valued features computing "
            "10 nuclear characteristics (radius, texture, perimeter, area, smoothness, "
            "compactness, concavity, concave points, symmetry, fractal dimension) across mean, "
            "standard error, and 'worst'."
        ),
        collection_process=(
            "Digitized micrographs of FNA glass slides from breast mass patients at the "
            "University of Wisconsin Hospitals, Madison. Cell boundaries determined via X-window "
            "program (Xcyt)."
        ),
        preprocessing_and_cleaning=(
            "Standardized feature scaling fitted strictly on training splits. No missing values "
            "in original WDBC."
        ),
        uses_and_limitations=(
            "Benchmark dataset for algorithmic verification only. Extremely high signal-to-noise "
            "ratio untypical of routine screening. Completely lacks patient demographic variables."
        ),
        distribution_and_licensing="Public domain / open research use.",
        maintenance_plan="Archival benchmark; preserved in Scikit-Learn standard distribution.",
    )


def get_model_card_mammography() -> ModelCard:
    """Return Model Card for the UCI Mammography RAA System."""
    return ModelCard(
        model_name="Risk-Aware Abstention Mammographic Mass Decision Agent",
        model_version="1.0.0-rc",
        architecture_overview=(
            "Composite ensemble: 300-tree Scikit-Learn RandomForestClassifier primary predictor; "
            "30-member bootstrap ensemble for predictive disagreement (U); 200-tree "
            "IsolationForest for novelty scoring (A); asymmetric consequence weighting (C); "
            "validation percentile routing policy."
        ),
        intended_use=(
            "Secondary triage prioritization and educational demonstration. Assisting clinical "
            "workflows by routing high-confidence cases to Automatic processing while escalating "
            "borderline cases."
        ),
        out_of_scope_uses=(
            "Standalone autonomous medical diagnosis, emergency patient discharge, direct patient "
            "self-diagnosis without qualified radiologist review."
        ),
        relevant_factors=(
            "Patient age, mass shape, mass margin, radiological breast tissue density. NOT "
            "trained on symptoms, family history, breast implants, or non-mass lesions."
        ),
        performance_metrics={
            "Held-out Test Accuracy": "73.1% (seed 42 split)",
            "Malignant Sensitivity": "61.8%",
            "Benign Specificity": "82.7%",
            "AUROC": "0.810",
            "Automatic Tier Coverage": "67.4% (130/193 cases at p70)",
            "Automatic Tier Error Rate": "20.0%",
            "Malignant False Negatives in Auto": "10 of 34 total test false negatives",
        },
        ethical_considerations=(
            "High error rate in Automatic tier (20%) reflects dataset limitations and confirms "
            "this prototype must never be used for actual patient care. Explanations are strictly "
            "grounded and rule-checked."
        ),
        caveats_and_recommendations=(
            "The model demonstrates the abstention *architecture*, not clinical efficacy. Any "
            "clinical application requires prospective multi-center trial validation on modern "
            "full-field digital mammography (FFDM) or tomosynthesis (DBT) data."
        ),
    )


def get_lifecycle_governance() -> dict[str, Any]:
    """Return concrete governance procedures across accountability, transparency, privacy."""
    return {
        "accountability_matrix": {
            "model_owner": (
                "Lead ML Research Engineer (responsible for code integrity, reproducible builds, "
                "and split hygiene)"
            ),
            "safety_officer": (
                "Clinical Safety Officer (responsible for consequence matrix, threshold "
                "sign-off, and claim boundaries)"
            ),
            "governance_lead": (
                "Information Governance Lead (responsible for privacy compliance and audit logs)"
            ),
        },
        "transparency_protocol": {
            "explanation_guarantee": (
                "Every inference produces twin grounded explanations (Class influence vs Routing "
                "risk) before action."
            ),
            "rule_checker": (
                "Rule-based regex engine verifies that outputs contain zero ungrounded clinical "
                "claims or diagnosis promises."
            ),
            "audit_logging": (
                "Immutable DecisionRecord captures model weights, thresholds, input values, "
                "and component scores."
            ),
        },
        "privacy_and_security": {
            "network_isolation": (
                "Inference and web UI run strictly on IPv6 loopback (::1). Zero external "
                "network egress."
            ),
            "data_persistence": (
                "Zero database or disk storage of patient intake responses. Ephemeral "
                "memory-only execution."
            ),
            "phi_minimization": (
                "System collects no direct identifiers (name, date of birth, NHS/MRN number)."
            ),
        },
        "lifecycle_management": {
            "drift_monitoring": (
                "Anomaly Isolation Forest acts as an in-line sentinel for covariate shift."
            ),
            "recalibration_triggers": (
                "Model requires re-benchmarking if validation risk distribution drifts by >10% "
                "Wasserstein distance."
            ),
            "decommissioning_criteria": (
                "Retire model immediately if data source is deprecated or hardware scanners "
                "change imaging physics."
            ),
        },
    }


def export_governance_artifacts(output_dir: Path = DEFAULT_GOVERNANCE_DIR) -> dict[str, Path]:
    """Serialize all governance artifacts to JSON files in the governance directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    # 1. Risk Register
    risk_file = output_dir / "risk_register.json"
    risk_data = [asdict(item) for item in get_risk_register()]
    risk_file.write_text(json.dumps(risk_data, indent=2), encoding="utf-8")
    paths["risk_register"] = risk_file

    # 2. Datasheets
    ds_mammo = output_dir / "datasheet_mammography.json"
    ds_mammo.write_text(
        json.dumps(asdict(get_dataset_datasheet_mammography()), indent=2), encoding="utf-8"
    )
    paths["datasheet_mammography"] = ds_mammo

    ds_wdbc = output_dir / "datasheet_wdbc.json"
    ds_wdbc.write_text(json.dumps(asdict(get_dataset_datasheet_wdbc()), indent=2), encoding="utf-8")
    paths["datasheet_wdbc"] = ds_wdbc

    # 3. Model Cards
    mc_mammo = output_dir / "model_card_mammography.json"
    mc_mammo.write_text(
        json.dumps(asdict(get_model_card_mammography()), indent=2), encoding="utf-8"
    )
    paths["model_card_mammography"] = mc_mammo

    # 4. Lifecycle Governance
    lg_file = output_dir / "lifecycle_governance.json"
    lg_file.write_text(json.dumps(get_lifecycle_governance(), indent=2), encoding="utf-8")
    paths["lifecycle_governance"] = lg_file

    return paths
