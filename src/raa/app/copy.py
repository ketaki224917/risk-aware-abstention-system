"""User-facing copy kept separate from Streamlit layout code."""

BANNER = "Research prototype. Not a medical device. Not for diagnosis."
PRIVACY = (
    "Do not enter names, IDs, symptoms, or demographic information. "
    "The app holds measurements in this browser session and does not save case inputs."
)
INPUT_HELP = (
    "This model uses numeric cell-nucleus measurements from the Wisconsin Diagnostic Breast "
    "Cancer dataset. Symptoms alone are not supported."
)
LIMITS = (
    "This is a methodological research prototype, not clinically validated. "
    "It cannot diagnose cancer, establish fairness, or estimate a calibrated probability of error."
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
        "The weighted score used by this prototype to route a case to Automatic, Assisted, "
        "or Human Review."
    ),
    "Abstention": (
        "The system routes a case for assistance or human review instead of returning it "
        "in the Automatic tier."
    ),
}
