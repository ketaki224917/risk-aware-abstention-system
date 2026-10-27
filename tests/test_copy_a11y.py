from raa.app.copy import BANNER, GLOSSARY, INPUT_HELP, INTAKE_REASON, INTAKE_RESULT, LIMITS, PRIVACY


def test_user_copy_keeps_safety_and_privacy_boundaries():
    assert BANNER == "Research prototype. Not a medical device. Not for diagnosis."
    assert "not clinically validated" in LIMITS.lower()
    assert "fairness" in LIMITS.lower()
    assert "contact details" in PRIVACY.lower()
    assert "symptoms alone are not supported" in INPUT_HELP.lower()
    assert "family history" in INPUT_HELP.lower()
    all_copy = " ".join((BANNER, PRIVACY, INPUT_HELP, LIMITS, *GLOSSARY.values())).lower()
    assert "you have cancer" not in all_copy
    assert "clinically proven" not in all_copy


def test_glossary_defines_uncertainty_and_synthetic_stress_limits():
    assert "not a calibrated error probability" in GLOSSARY["Model disagreement"]
    assert "synthetic feature shifts only" in GLOSSARY["Unusualness"]
    assert "not a clinical cost" in GLOSSARY["Cost of error"]


def test_four_question_intake_never_claims_a_compatible_prediction():
    assert "Human Review" in INTAKE_RESULT
    assert "no prediction made" in INTAKE_RESULT.lower()
    assert "not been trained or validated" in INTAKE_REASON
    assert "Malignant or Benign" in INTAKE_REASON
