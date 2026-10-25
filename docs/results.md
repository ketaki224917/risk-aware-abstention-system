# Results

Run `raa-20261025-01` was generated on 2026-10-25 with `uv run python -m raa.cli reproduce --run-id raa-20261025-01`. It contains 30 stratified splits and 3,420 pooled test cases. Results are under `results/runs/raa-20261025-01/`. The original source paper was not present, so targets are from the supplied prompt and some details remain assumptions.

The paper figures below came from the user-provided project specification; they are not locally verified. Results from actual runs will be stored by run ID under `results/runs/` and summarized here with commands and confidence intervals.

| Metric | Paper target | Reproduced |
|---|---:|---:|
| Baseline Random Forest error rate | ≈4.15% | 4.064% pooled; split 95% CI 3.480–4.708% |
| Automatic accepted-case error rate | ≈0.70% | 1.493% pooled; split 95% CI 1.058–1.894% |
| Automatic coverage | ≈70.7% | 68.538% pooled; split 95% CI 66.579–70.643% |
| Baseline false negatives routed away from Automatic | ≈81% | 90.588% pooled (77/85) |
| Isolation Forest AUROC, synthetic shift only | ≈0.91 | 0.731 pooled over 12 variants (paired case-bootstrap 95% CI 0.709–0.758); 0.921 (0.882–0.957) for the 10-feature, 2σ variant |
| Uncertainty-only selective accuracy | ≈99.39% | 99.301%; split 95% CI 98.973–99.597% |
| Full-policy selective accuracy | ≈99.30% | 98.507% pooled; split 95% CI 98.106–98.942% |
| Explanation checker injected-fault detection | Source figure not included | 100% (12/12); clean false-positive rate 0% (0/2) |

The paired split comparison gives uncertainty-only minus full-policy selective accuracy of +0.783 percentage points (95% bootstrap CI +0.296 to +1.294). This run supports the negative-finding direction but does not reproduce the full-policy target. See [the reconciliation](state/RECONCILIATION.md) and the run's CSV/JSON outputs. These are methodological benchmark results, not clinical evidence.
