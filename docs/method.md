# Method

## Data and split

Use `sklearn.datasets.load_breast_cancer`: 569 cases, 30 numeric features, target 0 malignant (212 cases) and target 1 benign (357 cases). Each evaluation seed produces a stratified 60/20/20 train/validation/test split; with the configured fractions, each test partition has 114 cases. There are 30 fixed seeds (`2026` through `2055`), yielding 3,420 pooled test cases. A new split refits all estimators.

## Prediction and risk

The main classifier is a 300-tree `RandomForestClassifier`. Predictive uncertainty is the population standard deviation of malignant-class probabilities from 30 Random Forests, each trained on a bootstrap sample of the training rows. Each member uses 50 trees as an explicit assumption because no member size was provided. The standard deviation is a disagreement signal; it is not a calibrated probability of prediction error.

An `IsolationForest` with 200 trees is fit on training features. The anomaly score is `-decision_function`, so larger values mean more unusual. For each split, uncertainty and anomaly min/max values are fit on validation component scores; transformed values are clipped to `[0,1]`. Consequence is already defined in `[0,1]` and does not require a fitted statistic. Its values (0 for malignant predictions, 1 for benign predictions) are assumptions, not clinical costs.

The full score is `R = 0.5 U + 0.2 A + 0.3 C`. Ablation scores renormalize the included components' original weights to sum to one. For each full or ablation policy, t70 and t90 are selected from that split's validation risk values using linear percentile interpolation:

- `R <= t70`: Automatic
- `t70 < R <= t90`: Assisted
- `R > t90`: Human Review

Thresholds are never fit on test data.

## Explanations

Inference produces an immutable `DecisionRecord` containing prediction, probability, normalized components, risk, thresholds, and routing. A deterministic template reads that record. A separate rule checker compares the rendered prediction, score, risk tier, decision level, caveats, and disclaimer against the same record and blocks overconfident clinical language. Explanation generation does not receive a mutation interface and cannot change prediction or routing.

## Evaluation

The 30-split runner reports classifier metrics and automatic coverage, accepted-case errors, review counts, false negatives routed away from Automatic, uncertainty ranking diagnostics, probability ECE, paired ablations, risk-coverage sweeps, and predeclared sensitivity grids. Confidence intervals are percentile bootstrap intervals over split-level estimates; ablations also report paired split differences against the full policy. Synthetic anomaly stress shifts seeded subsets of held-out test features by positive multiples of training-set standard deviations; the stress data is not used to fit the detector or policy.

Every reported table must be generated from the command and configuration recorded with its run ID. Paper target values are comparisons only.
