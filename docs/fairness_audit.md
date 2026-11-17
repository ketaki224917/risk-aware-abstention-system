# Careful Fairness Audit & Demographic Fairness Gap

## 1. Executive Summary & Critical Governance Statement

> [!CAUTION]
> **CRITICAL DEMOGRAPHIC FAIRNESS GAP**
> The subgroups evaluated in this audit are derived exclusively from available clinical and anatomical features (patient scan age and radiological tissue density). The UCI Mammographic Mass dataset contains **zero demographic attributes**—no race, ethnicity, socioeconomic status, geographic region, primary language, or scanner hardware vendor.
>
> While feature-based groupings reveal meaningful behavioral variation and error clustering across anatomical phenotypes, **THEY DO NOT ESTABLISH DEMOGRAPHIC FAIRNESS OR HEALTH EQUITY.** No claims of demographic parity, equalized odds, or algorithmic justice can be justified from this dataset. Full clinical deployment requires prospective multi-center auditing across demographically representative cohorts.

---

## 2. Methodology & Statistical Rigor

- **Evaluated Dataset**: UCI Mammographic Mass held-out test split ($n=193$, seed 42, 20% stratified sample).
- **Subgroup Partitions**:
  1. *Patient Age Brackets*:
     - Younger / Premenopausal: $\text{Age} < 50$ ($n=72$, 37.3% of cohort)
     - Core Screening Age: $50 \le \text{Age} < 65$ ($n=67$, 34.7% of cohort)
     - Older / Postmenopausal: $\text{Age} \ge 65$ ($n=54$, 28.0% of cohort)
  2. *Radiological Breast Tissue Density*:
     - Dense Tissue (BI-RADS Density codes 1 & 2: high density or iso-dense tissue, $n=60$, 31.1%)
     - Non-Dense / Fatty Tissue (BI-RADS Density codes 3 & 4: low density or fatty tissue, $n=133$, 68.9%)
  3. *Intersectional Subgroups*: Age bracket $\times$ Density cross-tabulations.
- **Uncertainty Quantification**: 95% two-sided Confidence Intervals are calculated for all proportions using the Wilson score method with continuity correction.

---

## 3. Subgroup Audit Findings (Held-Out Test Split, $n=193$)

| Subgroup Dimension | Subgroup Name | Sample $n$ | Malignant Prevalence | Baseline Error Rate [95% CI] | Malignant Sensitivity [95% CI] | Benign Specificity [95% CI] | Overall Referral Rate [95% CI] | Automatic Error Rate [95% CI] | FN Catch Rate |
|---|---|---|---|---|---|---|---|---|---|
| **Baseline** | Overall Cohort | 193 | 46.1% | 26.9% [21.2% - 33.6%] | 61.8% [51.4% - 71.2%] | 82.7% [74.3% - 88.8%] | 32.6% [26.4% - 39.5%] | 20.0% [14.0% - 27.7%] | **70.6%** (24/34) |
| **Age** | Age < 50 (Younger) | 72 | 19.4% | 25.0% [16.4% - 36.1%] | **14.3%** [4.0% - 39.9%] | 89.7% [79.2% - 95.2%] | 31.9% [22.3% - 43.4%] | 18.4% [10.0% - 31.4%] | **66.7%** (8/12) |
| **Age** | Age 50-64 (Core) | 67 | 43.3% | 29.9% [20.2% - 41.7%] | 69.0% [50.8% - 82.7%] | 71.1% [55.2% - 83.0%] | 34.3% [24.1% - 46.3%] | 22.7% [12.7% - 37.3%] | **66.7%** (6/9) |
| **Age** | Age $\ge 65$ (Older) | 54 | 85.2% | 25.9% [15.8% - 39.3%] | 71.7% [57.5% - 82.7%] | 100.0% [67.6% - 100.0%] | 31.5% [20.7% - 44.8%] | 21.6% [11.3% - 37.2%] | **76.9%** (10/13) |
| **Density** | Dense Tissue (1 & 2) | 60 | 46.7% | 31.7% [21.3% - 44.2%] | 57.1% [39.1% - 73.5%] | 78.1% [61.2% - 89.0%] | 36.7% [25.7% - 49.3%] | 23.7% [12.9% - 39.5%] | **66.7%** (8/12) |
| **Density** | Non-Dense (3 & 4) | 133 | 45.9% | 24.8% [18.2% - 32.8%] | 63.9% [51.4% - 74.8%] | 84.7% [74.7% - 91.2%] | 30.8% [23.7% - 39.1%] | 18.5% [11.9% - 27.6%] | **72.7%** (16/22) |
| **Intersection**| Younger & Dense | 34 | 20.6% | 29.4% [16.8% - 46.2%] | 28.6% [8.2% - 64.1%] | 81.5% [63.3% - 91.8%] | 38.2% [23.9% - 55.0%] | 23.8% [10.6% - 45.1%] | **60.0%** (3/5) |
| **Intersection**| Older & Dense | 14 | 85.7% | 28.6% [11.7% - 54.7%] | 66.7% [39.1% - 86.2%] | 100.0% [34.2% - 100.0%] | 28.6% [11.7% - 54.7%] | 30.0% [10.8% - 60.3%] | **75.0%** (3/4) |

---

## 4. Key Clinical Observations & Sample Limitations

### 4.1 Severe Sensitivity Disparity in Younger Patients
- In patients under age 50, malignant sensitivity of the raw classifier collapses to **14.3%** [4.0% - 39.9%]. Because breast cancer incidence is lower in younger women, the model disproportionately predicts benign, missing 12 of 14 cancers.
- **Impact of RAA Abstention**: The RAA framework successfully intercepted **66.7%** (8 of 12) of those false negatives, routing them away from the Automatic tier into Assisted and Human Review due to elevated bootstrap disagreement and anomaly scores.
- **Statistical Limitation**: The sample of malignant cases under age 50 is small ($n_{\text{malignant}} = 14$), resulting in a wide 95% confidence interval ($[4.0\%, 39.9\%]$). While the trend indicates sensitivity degradation in younger patients, exact effect sizes require larger sample sizes.

### 4.2 Tissue Density Masking Effects
- Error rates are elevated in dense breast tissue (**31.7%** vs **24.8%** in non-dense tissue). Dense tissue attenuates X-ray contrast, increasing morphological ambiguity.
- Consequently, the RAA policy refers dense tissue cases at a higher rate (**36.7%** vs **30.8%** in non-dense tissue), accurately mirroring the radiological challenge of dense breast screening.

### 4.3 Intersectional Subgroup Sample Scarcity
- Intersectional bins such as *Older & Dense* contain only 14 patients in the held-out split. The corresponding error rate confidence interval spans from **11.7% to 54.7%**.
- We report these intervals transparently to avoid making unsubstantiated statistical claims on micro-cohorts.

---

## 5. The Demographic Fairness Boundary

To maintain scientific integrity and prevent algorithmic bias washing:
1. **No Demographic Equivalence**: Subgroup breakdowns by age and breast density are physiological and anatomical markers. They must never be misconstrued as proxies for race, ethnicity, or socioeconomic equality.
2. **Missing Intersectional Data**: Women of color, particularly Black women, experience higher premenopausal breast cancer incidence and mortality. Because this single-institution German dataset lacks racial demographic tags, it is impossible to assess whether the sensitivity drop observed in young women disproportionately harms minoritized populations.
3. **Regulatory Recommendation**: Before any clinical translation, the system must undergo a formal Demographic Parity and Equalized Odds audit across diverse cohorts under NHS/FDA AI health equity governance frameworks.
