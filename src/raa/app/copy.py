"""User-facing copy and report-category choices for the RAA intake."""

PRIVACY = (
    "Do not enter names or contact details. Report details stay in this app session. "
    "If you request a Word report, its summary is generated on this computer. "
    "Nothing is saved unless you download the report."
)

INPUT_INTRO = (
    "Use the wording from a mammogram report. The model reads age and the three mass details "
    "below; each one is part of the prediction."
)
INPUT_HELP = (
    "This model is for a mass described in a mammogram report. If you do not have the report, "
    "or it does not describe a mass, choose that option and the result will go to Human Review."
)
REPORT_STATUS_LABEL = "Does the mammogram report describe a mass?"
REPORT_STATUS_OPTIONS = (
    "Yes, it describes a mass",
    "No, it does not describe a mass",
    "I do not have the report / not sure",
)
REPORT_HAS_MASS = REPORT_STATUS_OPTIONS[0]
REPORT_NO_MASS = REPORT_STATUS_OPTIONS[1]
REPORT_UNAVAILABLE = REPORT_STATUS_OPTIONS[2]
REPORT_DETAILS_NOTE = (
    "Enter the age at the scan and the report's descriptions. If a detail is unclear or not "
    "listed, choose Not sure / not listed; the system will send the case for Human Review."
)
AGE_LABEL = "Age when the mammogram was taken (years)"
SHAPE_QUESTION = "What shape does the report give for the mass?"
SHAPE_HELP = (
    "Use the report's category. The short descriptions explain the wording; do not guess if "
    "the report uses a different term. If it is unclear or missing, choose Not sure / not listed."
)
SHAPE_CHOICES = {
    "Round (circle-shaped)": 1,
    "Oval (egg-shaped)": 2,
    "Lobulated (rounded sections)": 3,
    "Irregular (uneven)": 4,
}
MARGIN_QUESTION = "How does the report describe the mass edge?"
MARGIN_HELP = (
    "The report may describe a clear edge, small bumps, a partly hidden edge, an unclear edge, "
    "or a spiky edge."
)
MARGIN_CHOICES = {
    "Clear and smooth (circumscribed)": 1,
    "Small bumps (microlobulated)": 2,
    "Partly hidden (obscured)": 3,
    "Unclear edge (ill-defined)": 4,
    "Spiky edge (spiculated)": 5,
}
DENSITY_QUESTION = "How does the report describe the mass density?"
DENSITY_HELP = "Choose the wording closest to the density category printed in the report."
DENSITY_CHOICES = {
    "High": 1,
    "Similar to nearby tissue": 2,
    "Low": 3,
    "Mostly fat-containing": 4,
}
UNKNOWN_REPORT_VALUE = "Not sure / not listed"

NO_ESTIMATE_COPY = (
    "This model needs a mammogram report that describes a mass. No benign/malignant class "
    "estimate was produced."
)
MODEL_INPUTS_COPY = (
    "The saved model uses four values: age at the mammogram and the report's mass shape, "
    "edge, and density. Use the mammogram report wording; do not guess these details."
)

LIMITS = (
    "This is a research project, not a clinical tool. Its model score is not a calibrated "
    "chance of cancer, and the dataset does not establish clinical performance or fairness."
)

GLOSSARY = {
    "Model disagreement": (
        "Variation in malignant-class scores across bootstrap Random Forests. "
        "It is an uncertainty signal, not a calibrated error probability."
    ),
    "Unusualness": (
        "How far the feature profile looks from the training data according to Isolation Forest. "
        "The paper's AUROC uses synthetic feature shifts only."
    ),
    "Cost of error": (
        "A design value for the predicted class. It is an assumed consequence weight, "
        "not a clinical cost."
    ),
    "Risk": (
        "The weighted score used by the RAA policy to route a case to Automatic, Assisted, "
        "or Human Review."
    ),
    "Abstention": (
        "The system routes a case for assistance or human review instead of returning it "
        "in the Automatic tier."
    ),
}
