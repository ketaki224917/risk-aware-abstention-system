# Viva guide

## Two-minute explanation

Risk-Aware Abstention combines a classifier with disagreement, unusualness, a consequence term, a risk score, and three routes: Automatic, Assisted, or Human Review. The original WDBC paper-aligned experiment remains separate from the user-facing app. For the app, a compatible mammogram report supplies four actual model inputs: age at the scan, mass shape, edge, and density. The app shows a benign/malignant mammographic-mass label estimate, the separate RAA route, and one-field sensitivity checks. Missing or unclear report details lead to Human Review; without a report describing a mass there is no class estimate. The held-out malignant sensitivity is 61.8% and Automatic-tier error is 20.0%, so the model is not suitable for health decisions. The optional local report writer cannot change the class or route.

## Ten-minute walkthrough

1. Open the dark app at localhost:8501 and point out the report-availability question.
2. Select that the mammogram report describes a mass, then enter scan age and the report's shape, edge, and density using the friendly labels.
3. Submit and read the model lean, explanation, and separate RAA route; confirm each of the four inputs reaches the saved model.
4. Show the one-field sensitivity checks and explain that they describe model behavior, not causes.
5. Open How the RAA route was chosen; describe disagreement, unusualness, consequence, weighted risk, and p70/p90 thresholds.
6. Open About this model and read held-out sensitivity and Automatic-tier error before discussing limits.
7. Generate a report and point out that the local language model writes prose only; deterministic result facts are included in the download.
8. Show the UCI model artifacts in results/mammographic_mass and distinguish them from the original WDBC results in results/runs.
9. Close with the no-diagnosis boundary and the dataset's limited held-out performance.

## Likely questions and answers

1. **What problem does RAA address?** It studies when a model result can be returned automatically and when assistance or human review is needed.
2. **What is abstention here?** Routing away from Automatic; the classifier's lean can still be shown as an unverified estimate.
3. **What datasets are used?** WDBC supports the paper-aligned experiment. UCI Mammographic Mass supports the user-facing report-input model.
4. **How many cases are in the app dataset?** 961 mammographic masses: 516 benign and 445 malignant labels.
5. **What inputs affect the app model?** Age, mass shape, margin (edge), and density from a mammogram report. BI-RADS is excluded because UCI marks it non-predictive.
6. **Why does the form ask for mammogram-report details instead of symptoms?** Those four fields are the available model inputs in the labeled dataset; the dataset has no symptom or family-history predictors.
7. **What does the classifier predict?** The benign or malignant severity label recorded for a mammographic mass, not a person's diagnosis.
8. **How is the app data split?** One fixed stratified 60/20/20 split with seed 42: 576 TRAIN, 192 validation, 193 TEST.
9. **How are missing report fields handled?** TRAIN-only imputation is applied to run the pipeline, and any incomplete user report is routed to Human Review.
10. **What happens without a mammogram report?** The app returns Human Review and no benign/malignant estimate.
11. **How is uncertainty estimated?** Standard deviation of malignant-class scores across 30 bootstrap Random Forest members.
12. **Is that a probability of error?** No. It is a disagreement signal, not a calibrated error probability.
13. **What does the anomaly score mean?** Larger values indicate inputs more unusual relative to the training data, based on Isolation Forest.
14. **Are consequence values clinical costs?** No. The paper specifies 0.4 for a predicted malignant class and 1.0 for predicted benign; these remain design assumptions.
15. **How is the combined risk computed?** R = 0.5U + 0.2A + 0.3C using normalized uncertainty, anomaly, and consequence components.
16. **How are default routes selected?** Validation p70 and p90 risk thresholds give Automatic, Assisted, and Human Review.
17. **How does the app explain an individual output?** It replaces one field at a time with a common TRAIN value and reports how the malignant-class score changes. This is model sensitivity, not a causal explanation.
18. **Can the LLM change a prediction?** No. It is called only when a report is requested and writes a short paragraph; model output and routing remain deterministic.
19. **Where does the report LLM run?** On the local computer through Ollama. The app does not call a hosted language model.
20. **What are the held-out app metrics?** Accuracy 73.1%, malignant sensitivity 61.8%, benign specificity 82.7%, AUROC 0.810.
21. **How reliable was the Automatic tier?** Its held-out error rate was 20.0%; 10 of 34 malignant false negatives were Automatic. This is unsuitable for health decisions.
22. **Does the project establish fairness?** No. The datasets and experiments do not establish demographic fairness.
23. **What is the contribution?** Integrating classification, risk signals, a three-level route, and explanations while reporting the coverage/error trade-off honestly.
24. **How are WDBC tables reproduced?** Run make reproduce in the locked environment; outputs are stored by run ID under results/runs.
25. **Is the app suitable for diagnosis?** No. It estimates a historical dataset label, has limited held-out sensitivity, and has no clinical validation.

## Claims not to make

- Do not describe an app result as a person's diagnosis.
- Do not describe this mammographic-mass label estimate as a prediction of a person's diagnosis.
- Do not claim clinical safety, fairness, or deployment readiness.
- Do not call disagreement a calibrated probability of error.
- Do not claim real-world anomaly performance from synthetic shifts.
- Do not claim the LLM report is validated or can change routing.
- Do not claim each RAA component improves classifier accuracy.

## How numbers are produced

The WDBC experiment outputs are versioned under results/runs/ and include 30 splits, ablations, stress tests, and explanation-checker results. The app model uses the fixed seed-42 UCI split; its held-out metrics, data hash, and model manifest are under results/mammographic_mass/. The app displays those saved values. No user-submitted inputs are written to either results directory.
