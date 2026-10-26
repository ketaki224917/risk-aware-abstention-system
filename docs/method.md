# Method

## Data and split

The project uses `sklearn.datasets.load_breast_cancer`: 569 cases, 30 numeric features, and target 0 for malignant (212 cases) or 1 for benign (357 cases). Each run uses stratified 60/20/20 train/validation/test partitions. The 30 repeated evaluation seeds are 0 through 29; the paper's separate illustrative split uses seed 42. The same split seed is used for both train/test and train/validation partitioning.

## Prediction and risk signals

The base classifier is a 300-tree `RandomForestClassifier`. Its random state is the split seed. Uncertainty is the population standard deviation of malignant probabilities from 30 Random Forest members, each with 50 trees and fit on a bootstrap sample of training rows. Member `b` uses the split seed plus its member index. The bootstrap standard deviation is disagreement, not a calibrated probability of error.

The anomaly model is a 200-tree `IsolationForest`. A `StandardScaler` is fit on training features and applied to all partitions. The raw anomaly score is `-score_samples`, so larger values mean more unusual. Its scaling range is the minimum and 99th percentile of training anomaly scores; transformed values are clipped to `[0, 1]`. Uncertainty is scaled as `min(U / validation_p95, 1)`. Consequence is 1.0 for a predicted benign class and 0.4 for a predicted malignant class. The paper describes these as design assumptions, not clinical costs.

The full score is `R = 0.5 U + 0.2 A + 0.3 C`. Ablations re-fit the same policy cutoffs on validation risks; U+A uses `0.7 U + 0.3 A`, and confidence-only uses `1 - max(class probability)`. The 70th and 90th percentiles of validation risk give the two thresholds:

- `R <= t70`: Automatic
- `t70 < R <= t90`: Assisted
- `R > t90`: Human Review

The paper does not specify every random generator detail. The exact split seed rule, member seed sequence, and stress generator seed are recorded in `config.yaml` and this run. They are deterministic implementation choices, not recovered source code.

## Synthetic stress test

For each of the 30 splits, every held-out case gets a signed 3-standard-deviation shift on 8 randomly selected features, with standard deviations computed on training data. Negative shifted feature values are clipped to zero. The Isolation Forest and standardizer are never fit on perturbed test data. Since the paper does not give a random generator seed or say whether the selected features/signs vary by case, the implementation uses a fixed run seed and independently samples features/signs per case. Results describe this synthetic stress only, not real-world distribution shift.

## Explanations

Inference produces an immutable `DecisionRecord` containing the predicted class, predicted-class confidence, uncertainty, anomaly score, consequence, risk, thresholds, decision level, and referral reason. A deterministic template reads this record; it cannot change prediction or routing. The checker tests the six paper-listed fault categories and checks record values, decision wording, the referral reason, and the prototype limitation. No live LLM is called.

## Evaluation and provenance

The reproducible run writes pooled and split-level classifier/selective metrics, decision-level error counts, confidence/uncertainty/anomaly/risk error-ranking AUROC, ECE, Brier score, paired ablations, risk-coverage sweeps, sensitivity grids, stress AUROC and escalation behavior, explanation fault results, tables, and figures. The main seed-42 split has its own metrics and records. Outputs are under `results/runs/<run-id>/`; environment and source fingerprints are stored in `metrics.json`.

See [the source map](state/SOURCE_MAP.md) for how the journal paper and five background references inform the implementation. Paper targets are comparisons, never tuning objectives.
