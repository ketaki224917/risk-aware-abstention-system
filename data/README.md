# Datasets

## UCI Mammographic Mass

- Source: [UCI Machine Learning Repository, Mammographic Mass](https://archive.ics.uci.edu/dataset/161/mammographic+mass)
- DOI: 10.24432/C53K6Z
- License: CC BY 4.0
- Data files: mammographic_masses.data and mammographic_masses.names
- 961 records: 516 benign and 445 malignant mass-severity labels.
- Predictors used here: age, mass shape, margin (edge), and density.
- BI-RADS is excluded: UCI describes it as non-predictive. Missing predictor values are imputed from TRAIN only.
- These are mammographic-mass report fields. They do not include symptoms, family history, height, weight, or gender.

This is an older, single-source dataset. The app estimates the mass severity label represented by these records; it does not diagnose a person or estimate cancer from symptoms alone. Held-out performance and split details are recorded separately in results/mammographic_mass/metrics.json.

## Duke BRCA screening table

brca.txt is the public Duke Statistical Science teaching dataset. It contains 987 screening mammograms from 2002 and whether a cancer diagnosis was recorded within 12 months. Its sparse positive outcomes and unsuitable target mean it is not used by the app model. See [Duke's dataset page](https://stat.duke.edu/datasets/brca) and results/clinical_candidate_audit/metrics.json.

## BrEaST clinical metadata (candidate only; not used by the app)

- Source: [TCIA Breast-Lesions-USG clinical data](https://www.cancerimagingarchive.net/collection/breast-lesions-usg/); dataset DOI 10.7937/9WKK-Q141; paper DOI 10.1038/s41597-024-02984-z.
- License: CC BY 4.0. The clinical workbook is `breast_lesions_usg_clinical.xlsx`.
- The 256 cases are adult women examined with breast ultrasound: 154 benign, 98 malignant, and 4 normal. The workbook records age, physician-observed signs, and an aggregated patient-symptom field.
- In the 252 benign/malignant rows, 41 ages, 45 Signs fields, and 94 Symptoms fields are marked unavailable; only 132 rows have all three fields.
- The Symptoms field does not provide the four separate self-reported questions in the app. Signs are clinician-observed. Height, weight, and gender variation are absent. The cohort is selected for ultrasound examination.
- This candidate is not used for user predictions. Reproduce the schema and completeness audit with `python scripts/audit_breast_symptom_candidate.py`; output is `results/br_east_candidate_audit/audit.json`.
