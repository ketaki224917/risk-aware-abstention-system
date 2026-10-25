# Limitations

This is a methodological prototype, not a medical device or clinically validated decision aid. It must not be used for real diagnosis.

1. **Predictive uncertainty is not calibrated error probability.** The ensemble standard deviation is a disagreement signal; it is not calibrated to the chance that a prediction is wrong.
2. **Risk weights and consequence values are design assumptions.** They are not derived from clinicians, patients, or measured clinical costs. The source paper and implementation were not available to recover alternative values.
3. **Anomaly detection is narrowly evaluated.** AUROC describes only the synthetic feature-shift stress test in this repository and does not establish real-world out-of-distribution performance.
4. **Explanations are templates.** The checker measures detection of defined injected faults. There is no validated live-LLM explanation result.
5. **Fairness cannot be established.** Demographic attributes are absent from the dataset. Proxy subgroup analysis is not demographic fairness evidence.
6. **No clinical validation or prospective evaluation exists.** The dataset is a historical, curated benchmark and does not represent deployment conditions, clinical workflow, or all populations.
7. **The dataset and model family are limited.** One small tabular benchmark and Random Forests do not establish generality to other diseases, sites, devices, prevalence levels, or model classes.
8. **Routing thresholds and workload are policy choices.** Validation percentiles and equal-count review workload do not measure staff time, clinical benefit, or optimal resource allocation.

Additional limitations will be appended after actual experiments. Any claim unsupported by reproduced results must be removed or marked as not supported in `docs/state/RECONCILIATION.md`.

## Observed in run `raa-20261025-01`

The reproduced full-policy automatic-case error was 1.493% pooled (split-level 95% interval 1.058–1.894%), compared with the supplied ≈0.70% target. Uncertainty-only selective accuracy was 99.301% versus 98.518% for the full policy. The stress-test AUROC pooled across the documented 12 variants was 0.731 (paired case-bootstrap 95% CI 0.709–0.758); the 10-feature, 2σ variant was 0.921 (0.882–0.957). The original stress recipe is unavailable, so the per-variant value is not evidence that the paper's exact experiment was reproduced.
