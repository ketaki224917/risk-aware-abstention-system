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
