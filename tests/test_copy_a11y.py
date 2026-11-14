from raa.app.copy import (
    DENSITY_CHOICES,
    DENSITY_HELP,
    GLOSSARY,
    INPUT_HELP,
    INPUT_INTRO,
    LIMITS,
    MARGIN_CHOICES,
    MARGIN_HELP,
    MODEL_INPUTS_COPY,
    PRIVACY,
    REPORT_STATUS_OPTIONS,
    SHAPE_CHOICES,
    SHAPE_HELP,
)


def test_questionnaire_copy_matches_model_inputs_and_privacy():
    assert len(REPORT_STATUS_OPTIONS) == 3
    assert set(SHAPE_CHOICES.values()) == {1, 2, 3, 4}
    assert set(MARGIN_CHOICES.values()) == {1, 2, 3, 4, 5}
    assert set(DENSITY_CHOICES.values()) == {1, 2, 3, 4}
    assert "each one is part of the prediction" in INPUT_INTRO.lower()
    assert "mammogram report" in INPUT_HELP.lower()
    assert "not sure" in SHAPE_HELP.lower()
    assert "report" in MARGIN_HELP.lower()
    assert "density" in DENSITY_HELP.lower()
    assert "age" in MODEL_INPUTS_COPY.lower()
    assert "density" in MODEL_INPUTS_COPY.lower()
    assert "nothing is saved" in PRIVACY.lower()
    assert "generated on this computer" in PRIVACY.lower()
    assert "not a calibrated" in LIMITS.lower()


def test_risk_glossary_keeps_uncertainty_and_cost_limits():
    assert "not a calibrated error probability" in GLOSSARY["Model disagreement"]
    assert "synthetic feature shifts only" in GLOSSARY["Unusualness"]
    assert "not a clinical cost" in GLOSSARY["Cost of error"]
