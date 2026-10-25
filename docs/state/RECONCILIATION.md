# Paper-vs-reproduced reconciliation

Run: `raa-20261025-01`, generated 2026-10-25 with `uv run python -m raa.cli reproduce --run-id raa-20261025-01`. The original paper and source repository were not present; paper numbers below are targets from the user-provided prompt. Main results pool 30 stratified splits (3,420 test cases). Confidence intervals are percentile bootstrap intervals over split-level estimates unless marked as stress-case bootstrap intervals.

| Metric | Paper | Reproduced (mean ± 95% CI or pooled) | Δ | Status | Explanation / experiment |
|---|---:|---:|---:|:---:|---|
| Random Forest error rate | ≈4.15% | pooled 4.064%; split mean 4.064% (3.480–4.708%) | −0.086 pp pooled | ✅ | 30 splits, 114 test cases each; target lies in split interval |
| Automatic accepted-case error | ≈0.70% | pooled 1.493%; split mean 1.482% (1.058–1.894%) | +0.793 pp pooled | ❌ | Fixed 0.5/0.2/0.3 weights and recorded consequence assumption; target not supported by this run |
| Automatic coverage | ≈70.7% | pooled 68.538%; split mean 68.538% (66.579–70.643%) | −2.162 pp pooled | ⚠️ | Close, but 70.7% is just above the split interval; no threshold retuning |
| Baseline false negatives routed away from Automatic | ≈81% | pooled 90.588% (77/85); split mean 90.115% (81.322–96.724%) | +9.588 pp pooled | ⚠️ | Higher than target; split interval is close to target at its lower edge |
| Isolation Forest AUROC, synthetic feature shift | ≈0.91 | pooled across all 12 variants 0.731 (paired case-bootstrap CI 0.709–0.758); 10 features shifted by 2σ: 0.921 (0.882–0.957) | Recipe-dependent | ⚠️ | The paper's perturbation recipe was absent. All variants are retained in `stress/stress_test.csv`; a single pooled value is not directly comparable to an unspecified paper recipe |
| Uncertainty-only selective accuracy | ≈99.39% | split mean 99.301% (98.973–99.597%) | −0.089 pp | ✅ | Approximate target is supported |
| Full-policy selective accuracy | ≈99.30% | pooled 98.507%; split mean 98.518% (98.106–98.942%) | −0.793 pp pooled | ❌ | Full policy is below target; not tuned to force a match |
| Full minus uncertainty-only selective accuracy | Uncertainty-only at least as good | paired mean −0.783 pp for full vs uncertainty-only; paired CI for uncertainty-only minus full +0.296 to +1.294 pp | — | ✅ | Reproduces the negative finding direction: uncertainty-only is better in this implementation |
| Explanation checker detection | Figure value not supplied | 100% (12/12 injected faults); clean false-positive rate 0% (0/2 templates) | Not comparable | ⚠️ | Only the six defined injected fault types and two deterministic records were evaluated |

## Findings and hypotheses tested

- The classifier error target is consistent with this run's split-level interval.
- The full-policy selective error target is not supported. The run reports the prespecified configuration and the 30-split ablation. The uncertainty-only policy has higher selective accuracy than the full policy, consistent with the prompt's negative-finding warning.
- A predeclared sensitivity grid perturbed each weight by −0.1/0/+0.1, varied consequence values over 9 combinations, and swept 8 ordered percentile pairs. These outputs are in `sensitivity.csv`. Some alternative weight combinations have higher selective accuracy, but the fixed main result remains unchanged; no alternative was selected to match the target.
- The supplied source did not specify consequence values, the number of trees per bootstrap member, or the synthetic perturbation recipe. ADR-003 records the assumptions and ADR-005 records why the fixed configuration was retained.

Author input is needed before rewriting the paper's unsupported full-policy and stress-test claims. See `docs/state/BLOCKERS.md`.
