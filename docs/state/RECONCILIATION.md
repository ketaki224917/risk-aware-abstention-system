# Paper-to-run reconciliation

## Source and implementation changes

The author's supplied journal paper specifies the values and methods that were missing from the original project prompt. The implementation now uses the paper's 0.4/1.0 consequence mapping, validation-p95 uncertainty scaling, training min/p99 anomaly scaling with training-fitted standardization, 30 split seeds 0-29, main split seed 42, 50 trees per bootstrap member, Isolation Forest with 200 trees, the 0.5/0.2/0.3 risk weights, 70th/90th validation-risk thresholds, and the stated signed 3σ, 8-feature stress-test recipe. The implementation's deterministic random generator and same-seed two-stage split choices are explicit assumptions because the paper provides no complete source code or RNG specification. See ADR-009 and [the source map](SOURCE_MAP.md).

## Thirty split comparison

Run: `raa-20261026-paper-aligned-01`, seeds 0-29, 3,420 held-out test rows. The environment used Python 3.13.17 and scikit-learn 1.9.1. Percentages below are calculated from logged run outputs; paper values are from Tables 5-10 and Sections 5.3-5.7 of the supplied journal paper.

| Metric | Journal paper | Source-aligned run | Difference / reading |
| --- | ---: | ---: | --- |
| Always-predict errors | 142/3,420 (4.15%); 86 FN | 142/3,420 (4.15%); 86 FN | Exact pooled counts match. |
| Automatic coverage | 70.7% (2,419 cases) | 70.41% (2,408 cases) | Close; 11 fewer automatic cases. |
| Automatic errors | 17/2,419 (0.70%); 16 FN | 13/2,408 (0.54%); 13 FN | Four fewer accepted errors in this rerun; report the run value and retain the paper value as its reported result. |
| Baseline FN routed away | 70/86 (81.4%) | 73/86 (84.9%) | Three more FNs routed away. |
| Mean selective accuracy | 99.30% ± 0.70 | 99.465% ± 0.702 | Both show strong accepted-case accuracy; coverage must be read alongside it. |
| Mean automatic coverage | 70.7% ± 6.0 | 70.41% ± 5.33 | Close. |
| Error-ranking AUROC: confidence | 0.897 | 0.8968 pooled | Close. |
| Error-ranking AUROC: uncertainty | 0.890 | 0.8889 pooled | Close. |
| Error-ranking AUROC: Isolation Forest | 0.471 | 0.4709 pooled | Close; anomaly score does not rank clean-data classifier errors. |
| Error-ranking AUROC: U+A | 0.856 | 0.8685 pooled | 0.0125 higher in this run. |
| Error-ranking AUROC: full risk | 0.879 | 0.8759 pooled | Close. |
| Uncertainty-only mean selective accuracy | 99.39% ± 0.69 | 99.385% ± 0.704 | Close. |
| Confidence-only mean selective accuracy | 99.30% ± 0.77 | 99.303% ± 0.777 | Close. |
| Full policy mean selective accuracy | 99.30% ± 0.70 | 99.465% ± 0.702 | Higher in this run; paired uncertainty-only minus full is -0.080 pp (95% CI -0.206 to +0.008 pp). |

The full policy sends 651 cases (19.0%) to Assisted and 361 (10.6%) to Human Review. Their error rates are 8.29% and 20.78%; they contain 13 and 60 false negatives, respectively. Automatic contains 13 errors, all false negatives. Paper Table 6 reports 658 Assisted and 343 Human Review cases, with 44 and 81 errors. The total review count and automatic count are similar, but the division between review tiers and error counts differs.

## Main seed-42 split

The paper's Table 4 reports 6 baseline errors (3 FN, 3 FP), 76/114 Automatic, 19 Assisted, 19 Human Review, zero Automatic errors, and all 3 FN routed away. This run matches the baseline counts, automatic count, automatic selective accuracy, total 38 referred cases, and FN routing. The run assigns 14 cases to Assisted and 24 to Human Review, compared with the paper's 19/19. It also yields validation thresholds 0.4569/0.6048, compared with the paper's 0.377/0.564. The original RNG/source code is unavailable, so the threshold and tier split discrepancy is recorded rather than tuned away.

## Synthetic feature-shift stress test

The paper reports mean ± SD AUROC of 0.911 ± 0.019 for Isolation Forest, 0.804 ± 0.032 for uncertainty, and 0.814 ± 0.028 for combined risk. The source-aligned run reports 0.912 ± 0.020, 0.803 ± 0.035, and 0.846 ± 0.025. The Isolation Forest and uncertainty results closely match; the combined-risk AUROC is 0.032 higher. In the source-aligned run, automatic coverage falls from 70.4% on clean cases to 9.8% on shifted cases (90.2% escalated), compared with 14.1% automatic (85.9% escalated) in paper Table 9. The perturbed always-predict accuracy is 92.9% ± 2.4 versus 93.5% ± 2.1 in the paper. The paper does not specify RNG details, and these differences remain visible in the comparison.

The paired cluster-bootstrap pooled AUROC intervals, which account for repeated dataset rows across split seeds, are 0.892-0.927 for the anomaly score, 0.778-0.828 for uncertainty, and 0.826-0.865 for full risk. These intervals are additional analysis and are not values reported by the paper.

## Explanation checker

On the paper's main seed-42 test split, all 114 deterministic explanations pass and the clean false-positive rate is 0/114. The checker detects all 570 injected faults: 114 wrong levels, 114 wrong classes, 114 altered numeric values, 114 unsupported diagnostic claims, 38 dropped referral reasons, and 76 policy contradictions. This reproduces the six fault categories and exact injected counts in paper Table 10. It does not measure live-LLM reliability.

## Overall conclusion

The source-aligned run reproduces the reported baseline counts, closely reproduces the key error-ranking AUROCs and the Isolation Forest stress AUROC, and shows a comparable coverage/accuracy trade-off. It does not reproduce the exact 30-split accepted-error count, the main-split assisted/human division or thresholds, or the combined-risk stress AUROC and escalation rate. Keep the run's values and the paper's values labeled separately. No parameter was tuned to target values.
