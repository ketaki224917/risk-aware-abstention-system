# Questionnaire demo source data

`brca.txt` is the public Duke Statistical Science BRCA teaching dataset. It contains 987
screening mammograms from 2002 and records whether a cancer diagnosis was made within 12 months.

Source and field definitions: <https://stat.duke.edu/datasets/brca>

The demo uses age-band indicators, family history, prior breast biopsy/surgery, and a symptom
indicator defined only as lump or nipple discharge. It excludes reader ID, recall, screening
recommendation fields, and breast-density fields. The outcome means a cancer diagnosis was
recorded within 12 months after screening; it is not a benign/malignant pathology classification
or a current diagnosis. The file has 37 cancer outcomes among 987 records, so estimates from it
are unstable and unsuitable for clinical use.
