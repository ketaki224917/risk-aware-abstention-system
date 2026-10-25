# Viva guide

## Two-minute explanation

Risk-Aware Abstention is a methodological prototype for deciding when a classifier prediction should be automated and when a person should review it. On the Wisconsin Diagnostic Breast Cancer benchmark, a 300-tree Random Forest predicts malignant versus benign. A 30-member bootstrap Random Forest ensemble supplies disagreement as an uncertainty signal, and a training-fitted Isolation Forest supplies an anomaly score. The two scores are normalized from validation data; a design-assumption consequence value is combined with them using fixed weights to form a risk score. Validation 70th and 90th percentiles route test cases to Automatic, Assisted, or Human Review. A frozen structured decision record grounds a deterministic explanation, and a rule checker flags injected inconsistencies. The explanation layer cannot change the prediction or route. This is not clinically validated, does not establish fairness, and does not calibrate ensemble disagreement as probability of error. The main contribution is system integration and measured coverage/workload trade-offs, including honest ablations; base methods are established techniques.

## Ten-minute walkthrough

1. Show the repository map, project prompt, `config.yaml`, and the run ID in `results/runs/`.
2. Explain the stratified 60/20/20 split and show that only training data fits models; validation fits component normalization and thresholds.
3. Show the Random Forest prediction, malignant probability, bootstrap disagreement, anomaly score, and consequence assumption.
4. Derive the weighted risk expression and explain each input's normalization.
5. Route an example using t70/t90 and distinguish prediction from routing.
6. Inspect a `DecisionRecord`, template, and checker fault injection; show that explanations are read-only.
7. Walk through pooled test metrics, split-level intervals, risk-coverage/workload, and paired ablation differences.
8. Explain the synthetic shift recipe and its limited meaning.
9. Close with limitations and the exact list of claims that are out of scope.

## Likely questions and answers

1. **What problem does RAA address?** It studies when a model prediction should be automatic and when a case should receive assisted or human review.
2. **What is abstention here?** Routing away from automatic acceptance; the classifier prediction itself remains visible.
3. **What dataset is used?** The scikit-learn Wisconsin Diagnostic Breast Cancer dataset, 569 rows and 30 numeric features.
4. **How is the data split?** Stratified 60/20/20, with a fresh split and refit for each of 30 fixed seeds.
5. **Why is test data held out?** To avoid using final evaluation cases to fit models, normalization, or thresholds.
6. **What classifier is used?** A 300-tree Random Forest.
7. **How is uncertainty estimated?** Standard deviation of malignant probabilities across 30 bootstrap Random Forest members.
8. **Is that a probability of error?** No. It is a predictive disagreement signal and is not calibrated as an error probability.
9. **What does the Isolation Forest score mean?** Larger values indicate more unusual cases after negating scikit-learn's normality score.
10. **How is anomaly detection evaluated?** A synthetic feature shift on held-out cases, not real deployment drift.
11. **What is consequence?** A design-assumption value attached to the predicted class; the prompt says benign predictions receive greater consequence.
12. **Are the consequence values clinical costs?** No. The source values were unavailable, so 0/1 is explicitly logged as an assumption.
13. **Why normalize on validation?** To keep the test partition untouched while mapping U and A into comparable bounded ranges.
14. **How are thresholds chosen?** The validation risk's 70th and 90th percentiles.
15. **What are the three routes?** Automatic at or below t70, Assisted above t70 through t90, Human Review above t90.
16. **Can an explanation change the model decision?** No. It reads a frozen record after prediction and routing are complete.
17. **How are explanations generated?** Deterministic templates; no live LLM result is claimed.
18. **What does the checker test?** Prediction, routing, risk tier and score wording, caveats, disclaimer, and overconfident clinical language.
19. **What does a fault-detection rate mean?** Detection on the defined injected faults only; it is not broad proof of explanation truthfulness.
20. **Does the project establish fairness?** No. The dataset has no demographic attributes.
21. **What if uncertainty-only beats the full system?** Report that negative result; do not claim every component improves accuracy.
22. **How is workload measured?** Assisted and Human Review case counts/fractions are reported separately; their unweighted sum is review workload, not staff time.
23. **What is the contribution?** Integration, the three-level policy, negative-aware ablation, grounded non-mutating explanations, and coverage/workload analysis.
24. **What is required to reproduce a table?** The locked environment, `make reproduce`, its run ID, saved split cache, CSV/JSON output, and seeds/configuration.
25. **Is the system suitable for diagnosis?** No. It is a research prototype with no clinical validation and must not be used for real diagnosis.

## Claims not to make

- No fairness or clinical safety claim.
- No calibrated probability-of-error claim for ensemble disagreement.
- No real-world anomaly detection claim from a synthetic stress test.
- No validated live-LLM explanation claim.
- No claim that every component improves accuracy or that the base algorithms are novel.
- No numeric result until a logged run has generated it.

## How numbers are produced

The experiment command and configuration are saved with each run ID. `per_split.csv` contains 30 split-level estimates; `metrics.json` contains split means, standard deviations, bootstrap 95% intervals, and pooled case metrics. Ablation differences are paired by seed. Stress AUROC is evaluated on clean versus synthetic shifted held-out cases. Checker rates are computed over the enumerated injected faults and clean templates.
