# Limitations

This is a methodological prototype, not a medical device or clinically validated decision aid. It must not be used for real diagnosis.

1. **Predictive uncertainty is not calibrated error probability.** The bootstrap ensemble standard deviation is a disagreement signal.
2. **Risk weights and consequence values are design assumptions.** The values and weights follow the supplied journal paper, but they are not derived from clinicians, patients, or measured clinical costs.
3. **Anomaly detection is narrowly evaluated.** AUROC describes one synthetic signed feature-shift experiment; it does not establish performance under real-world distribution shift.
4. **Explanations are deterministic templates.** Checker results describe only the enumerated injected faults. There is no live-LLM faithfulness or fluency result.
5. **Fairness cannot be established.** Demographic attributes are absent from this dataset. Proxy subgroup analysis is not demographic fairness evidence.
6. **No clinical validation or prospective evaluation exists.** This historical benchmark does not represent deployment conditions, clinical workflow, or the range of patient populations.
7. **The dataset and model family are limited.** One small tabular benchmark and Random Forest models do not establish generality to other diseases, sites, devices, prevalence levels, or model classes.
8. **Routing thresholds and workload are policy choices.** Validation percentiles and case counts do not measure staff time, clinical benefit, or optimal resource allocation.
9. **Exact original implementation provenance is unavailable.** The author supplied the journal paper, but not the original source repository or raw experiment archive. Random generator details omitted by the paper are explicit deterministic implementation choices.

The latest reproduced values and any differences from the journal paper are recorded in `docs/state/RECONCILIATION.md` and `docs/results.md`.
