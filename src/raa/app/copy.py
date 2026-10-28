"""User-facing copy kept separate from Streamlit layout code."""

BANNER = "Research prototype. Not a medical device. Not for diagnosis."
PRIVACY = (
    "Do not enter names, IDs, or contact details. Health and gender answers stay in this "
    "local app session and are not saved to disk. The local LLM receives fixed status text, "
    "not your answers. A downloaded report includes your answers."
)
INTAKE_LLM_NOTE = (
    "The local LLM explains the fixed Human Review status. It does not see your answers and "
    "cannot make or change a prediction."
)
INTAKE_LLM_FALLBACK = (
    "The prototype returned Human Review because its current model cannot assess these "
    "questionnaire inputs. No class estimate was produced."
)
INTAKE_REPORT_LABEL = "Download intake result report"

INPUT_HELP = (
    "The current Random Forest uses numeric cell-nucleus measurements from the Wisconsin "
    "Diagnostic Breast Cancer dataset. It cannot use age, symptoms, family history, or medical "
    "history to produce a classification. Symptoms alone are not supported."
)
INTAKE_TITLE = "Breast health questionnaire"
INTAKE_INTRO = (
    "Answer five basic questions, then choose an answer for each of four symptom questions."
)
INTAKE_MODEL_LIMIT = (
    "This research prototype cannot use these answers to predict cancer. Submitting the form "
    "returns Human Review with no prediction."
)
INTAKE_RESULT = "\U0001f534 Human Review \u2014 no prediction made."
INTAKE_REASON = (
    "The current Random Forest uses numeric cell-nucleus measurements. It has not been trained "
    "or validated on age, height, weight, gender, history, or these symptom answers."
)
INTAKE_SCOPE = (
    "Here, Human Review means the prototype could not assess these inputs. It is not a medical "
    "assessment, referral, or diagnosis."
)
INTAKE_BASIC_LABEL = "Basic health details"
INTAKE_AGE_LABEL = "Age (years)"
INTAKE_HEIGHT_LABEL = "Height (cm)"
INTAKE_WEIGHT_LABEL = "Weight (kg)"
INTAKE_GENDER_LABEL = "Gender"
INTAKE_GENDER_OPTIONS = (
    "Woman",
    "Man",
    "Non-binary",
    "Another identity",
    "Prefer not to say",
)
INTAKE_HISTORY_LABEL = "Breast and family history"
INTAKE_HISTORY_QUESTION = (
    "Have you or a close family member had a breast condition, breast surgery or treatment, "
    "or breast cancer?"
)
INTAKE_HISTORY_OPTIONS = ("Yes", "No", "Not sure")
INTAKE_SYMPTOMS_LABEL = "Four symptom questions"
INTAKE_SYMPTOM_QUESTIONS = (
    ("symptom_lump", "Do you have a new breast lump?", "Lump"),
    ("symptom_swelling", "Have you noticed breast swelling?", "Breast swelling"),
    ("symptom_skin_changes", "Have you noticed changes to breast skin?", "Skin changes"),
    ("symptom_nipple_changes", "Have you noticed changes to a nipple?", "Nipple changes"),
)
INTAKE_SYMPTOM_OPTIONS = ("Yes", "No", "Not sure")
INTAKE_SUBMIT = "Review my answers"
INTAKE_MISSING = "Please complete the five basic fields and answer all four symptom questions."
INTAKE_AGE_ERROR = "Enter an age as a whole number from 1 to 120."
INTAKE_MEASUREMENTS_ERROR = "Enter height from 50 to 250 cm and weight from 1 to 300 kg."

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
