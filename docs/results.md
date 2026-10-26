# Results

Run `raa-20261026-paper-aligned-01` was produced on 2026-10-26 with Python 3.13.17 and scikit-learn 1.9.1 using `uv run python -m raa.cli reproduce --run-id raa-20261026-paper-aligned-01`. It contains 30 stratified splits (seeds 0-29) and 3,420 held-out test rows. Outputs are in `results/runs/raa-20261026-paper-aligned-01/`; machine-readable metrics and environment fingerprints are in `metrics.json`.

## Thirty-split results

| Metric | Source-aligned run | Journal paper | Notes |
| --- | ---: | ---: | --- |
| Always-predict errors | 142/3,420 (4.15%); 86 FN | 142/3,420 (4.15%); 86 FN | Exact pooled counts match. |
| Automatic coverage | 2,408/3,420 (70.41%; split mean 70.41%, 95% CI 68.45-72.28%) | 2,419/3,420 (70.7%) | Close. |
| Automatic errors | 13/2,408 (0.54%; split mean 0.535%, 95% CI 0.320-0.775%); 13 FN | 17/2,419 (0.70%); 16 FN | Four fewer accepted errors in this run. |
| Baseline false negatives routed away from Automatic | 73/86 (84.88%) | 70/86 (81.4%) | Three more routed away. |
| Mean full-policy selective accuracy | 99.465% ± 0.702 (95% CI 99.225-99.680%) | 99.30% ± 0.70 | Both must be read with coverage. |
| Mean uncertainty-only selective accuracy | 99.385% ± 0.704 (95% CI 99.143-99.627%) | 99.39% ± 0.69 | Close. |
| Mean confidence-only selective accuracy | 99.303% ± 0.777 (95% CI 99.024-99.557%) | 99.30% ± 0.77 | Close. |
| Pooled error-ranking AUROC: confidence / uncertainty / U+A / full risk / anomaly | 0.8968 / 0.8889 / 0.8685 / 0.8759 / 0.4709 | 0.897 / 0.890 / 0.856 / 0.879 / 0.471 | Close; U+A is 0.0125 higher. |
| Expected calibration error, all cases | 0.0509 ± 0.0087 | 0.042 ± 0.011 | Higher in this run. |
| Brier score, all cases | 0.0329 ± 0.0086 | 0.033 ± 0.008 | Close. |

The paired split difference in selective accuracy (uncertainty-only minus full) is -0.080 percentage points (95% bootstrap CI -0.206 to +0.008). This interval includes zero; the run does not establish a meaningful accuracy ranking between the two. The reported paper's negative finding that uncertainty supplies most of the selective benefit remains consistent with the ablations.

## Main split, seed 42

The baseline has 6 errors (3 FN, 3 FP), matching the journal paper. The policy assigns 76/114 cases to Automatic with zero errors, sends all 3 FN away from automatic acceptance, and refers 38 cases total. The run assigns 14 cases to Assisted and 24 to Human Review; the paper reports 19 and 19. The accepted ECE is 0.0124, close to the paper's 0.012; Brier score is 0.0373, close to the reported 0.037. Run thresholds are 0.4569 and 0.6048, versus the paper's 0.377 and 0.564. See `main_split_metrics.json` and `explanations/main_split_records.csv`.

## Synthetic shift and explanation checker

| Metric | Source-aligned run | Journal paper |
| --- | ---: | ---: |
| Isolation Forest shift AUROC, mean ± SD | 0.912 ± 0.020 (pooled cluster-bootstrap 95% CI 0.892-0.927) | 0.911 ± 0.019 |
| Uncertainty shift AUROC, mean ± SD | 0.803 ± 0.035 (pooled cluster-bootstrap 95% CI 0.778-0.828) | 0.804 ± 0.032 |
| Full-risk shift AUROC, mean ± SD | 0.846 ± 0.025 (pooled cluster-bootstrap 95% CI 0.826-0.865) | 0.814 ± 0.028 |
| Shifted automatic coverage | 9.77% ± 5.10; 90.23% escalated | 14.1% ± 5.4; 85.9% escalated |
| Shifted always-predict accuracy | 92.87% ± 2.39 | 93.5% ± 2.1 |
| Explanation checker | 114/114 clean pass; 0/114 false positives; 570/570 injected faults detected | 114/114 clean pass; all fault types in Table 10 detected |

The stress test follows the journal's signed 3σ shift on 8 randomly chosen features per case, clipped at zero. Exact feature/sign RNG details are not specified in the paper; the deterministic seed is an implementation choice. The shift results are synthetic and do not establish real-world OOD performance. Checker fault detection describes only the tested, rule-based fault set and is not a live-LLM reliability estimate.

See [the paper reconciliation](state/RECONCILIATION.md), [limitations](limitations.md), and [source map](state/SOURCE_MAP.md). The result is a methodological benchmark, not clinical evidence.
