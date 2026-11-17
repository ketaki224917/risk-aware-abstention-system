"""Tests for AI impact assessment, risk register, datasheets, and model cards."""

from __future__ import annotations

import json
from pathlib import Path

from raa.governance import (
    DatasetDatasheet,
    ModelCard,
    RiskItem,
    export_governance_artifacts,
    get_dataset_datasheet_mammography,
    get_dataset_datasheet_wdbc,
    get_lifecycle_governance,
    get_model_card_mammography,
    get_risk_register,
)


def test_risk_register_completeness_and_schema():
    register = get_risk_register()
    assert len(register) >= 6
    risk_ids = [item.risk_id for item in register]
    assert "RISK-01" in risk_ids
    assert "RISK-04" in risk_ids  # Privacy
    assert "RISK-06" in risk_ids  # LLM report safety

    for item in register:
        assert isinstance(item, RiskItem)
        assert item.pre_mitigation_severity in ("Catastrophic", "Critical", "Moderate", "Low")
        assert len(item.mitigations) > 0
        assert len(item.responsible_owner) > 0
        assert len(item.residual_risk) > 0


def test_dataset_datasheets_conform_to_schema():
    mammo_ds = get_dataset_datasheet_mammography()
    wdbc_ds = get_dataset_datasheet_wdbc()
    for ds in (mammo_ds, wdbc_ds):
        assert isinstance(ds, DatasetDatasheet)
        assert len(ds.motivation) > 0
        assert len(ds.composition) > 0
        assert len(ds.collection_process) > 0
        assert len(ds.uses_and_limitations) > 0


def test_model_card_mammography_metrics_and_ethics():
    mc = get_model_card_mammography()
    assert isinstance(mc, ModelCard)
    assert "RandomForestClassifier" in mc.architecture_overview
    assert "73.1%" in mc.performance_metrics["Held-out Test Accuracy"]
    assert "61.8%" in mc.performance_metrics["Malignant Sensitivity"]
    assert len(mc.ethical_considerations) > 0
    assert len(mc.caveats_and_recommendations) > 0


def test_lifecycle_governance_structure():
    lg = get_lifecycle_governance()
    assert "accountability_matrix" in lg
    assert "transparency_protocol" in lg
    assert "privacy_and_security" in lg
    assert "lifecycle_management" in lg
    assert "loopback" in lg["privacy_and_security"]["network_isolation"]


def test_export_governance_artifacts(tmp_path: Path):
    paths = export_governance_artifacts(tmp_path)
    assert set(paths.keys()) == {
        "risk_register",
        "datasheet_mammography",
        "datasheet_wdbc",
        "model_card_mammography",
        "lifecycle_governance",
    }
    for file_path in paths.values():
        assert file_path.is_file()
        content = json.loads(file_path.read_text(encoding="utf-8"))
        assert isinstance(content, (dict, list))
