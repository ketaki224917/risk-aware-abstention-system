"""User-facing copy kept separate from Streamlit layout code."""

BANNER = "Research prototype. Not a medical device. Not for diagnosis."
PRIVACY = (
    "Do not enter names, IDs, or contact details. Inputs stay in this local app session and "
    "are not saved to disk. Four-question intake answers are not passed to the current classifier."
)
INPUT_HELP = (
    "The current Random Forest uses numeric cell-nucleus measurements from the Wisconsin "
    "Diagnostic Breast Cancer dataset. It cannot use age, symptoms, family history, or medical "
    "history to produce a classification. Symptoms alone are not supported."
)
INTAKE_TITLE = "Four-question intake"
INTAKE_INTRO = (
    "Answer all four questions. The app will not make a Malignant or Benign prediction "
    "from these answers."
)
INTAKE_MODEL_LIMIT = (
    "The current model was trained on numeric cell-nucleus measurements, not these four inputs. "
    "Submitting them cannot produce a model prediction."
)
INTAKE_RESULT = "🔴 Human Review — no prediction made."
INTAKE_REASON = (
    "The existing Random Forest has not been trained or validated on age, symptoms, family "
    "history, and medical history. A compatible labeled dataset and new model training and "
    "validation are required before Malignant or Benign outputs can be generated "
    "from these fields."
)
INTAKE_SCOPE = (
    "Here, Human Review means the prototype could not assess these inputs. It is not a medical "
    "assessment, referral, or diagnosis."
)
INTAKE_AGE_LABEL = "Age (years)"
INTAKE_SYMPTOMS_LABEL = "Symptoms"
INTAKE_FAMILY_LABEL = "Family History"
INTAKE_MEDICAL_LABEL = "Medical History"
INTAKE_SUBMIT = "Review answers"
INTAKE_MISSING = "Please complete all four fields before continuing."
INTAKE_AGE_ERROR = "Enter age as a whole number from 1 to 120."
INTAKE_SYMPTOM_OPTIONS = (
    "Lump",
    "Breast swelling",
    "Skin changes",
    "Nipple changes",
    "No symptoms",
)
INTAKE_HISTORY_OPTIONS = ("Yes", "No", "Not sure")
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
