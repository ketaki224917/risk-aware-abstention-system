from raa.app.copy import (
    GLOSSARY,
    INPUT_HELP,
    INTAKE_HISTORY_OPTIONS,
    INTAKE_SYMPTOM_OPTIONS,
    INTAKE_SYMPTOM_QUESTIONS,
    LIMITS,
    PRIVACY,
)


def test_questionnaire_copy_matches_model_inputs_and_privacy():
    assert INTAKE_HISTORY_OPTIONS == ("Yes", "No", "Not sure")
    assert INTAKE_SYMPTOM_OPTIONS == ("Yes", "No", "Not sure")
    assert len(INTAKE_SYMPTOM_QUESTIONS) == 4
    assert "mammogram report" in INPUT_HELP.lower()
    assert "report context only" in INPUT_HELP.lower()
    assert "nothing is saved" in PRIVACY.lower()
    assert "ollama on this computer" in PRIVACY.lower()
    assert "not a calibrated" in LIMITS.lower()


def test_risk_glossary_keeps_uncertainty_and_cost_limits():
    assert "not a calibrated error probability" in GLOSSARY["Model disagreement"]
    assert "synthetic feature shifts only" in GLOSSARY["Unusualness"]
    assert "not a clinical cost" in GLOSSARY["Cost of error"]
