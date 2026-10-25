# Decisions

## ADR-001: Treat workspace as a fresh implementation [DECISION] Date: 2026-10-25 Status: active
Context: Initial inventory found no project files, paper, data archive, results, or Git history.
Options considered: Guess at an existing code path; or record that the original implementation cannot be inspected and create a new implementation from the supplied specification.
Decision and why: Treat this as a fresh implementation. Do not claim that any existing path produces paper results, and do not claim reproduction until an actual run produces evidence.
Consequences / how to reverse: Results from this implementation must be clearly separated from paper target values. If the original source or paper is later supplied, inventory it and supersede this ADR with evidence.

## ADR-002: Preserve the prompt as repository instructions [DECISION] Date: 2026-10-25 Status: active
Context: User's prompt explicitly requests that it be saved at the repository root as `AGENTS.md`.
Options considered: Summarize it; or copy the attachment without changing its content.
Decision and why: Copy the attachment verbatim so subsequent sessions retain the full project specification.
Consequences / how to reverse: Edit only through a follow-up instruction or a superseding decision.

## ADR-003: Record unspecified risk-component values as explicit assumptions [ASSUMPTION] Date: 2026-10-25 Status: active
Context: The supplied prompt specifies that benign predictions carry a higher consequence but does not provide numeric consequence values or bootstrap member size. The source paper/code was absent.
Options considered: Invent hidden values; tune values to paper targets; or choose transparent bounded values and label the choice.
Decision and why: Use C(predicted malignant)=0 and C(predicted benign)=1, and 50 trees per bootstrap member. These are simple bounded assumptions that preserve the specified ordering. They are not clinically derived. Use the prompt's fixed 0.5/0.2/0.3 risk weights.
Consequences / how to reverse: All values are in config.yaml and consequence variations are logged in sensitivity.csv. Replace only with source-backed values and a superseding ADR; never tune to force target metrics.

## ADR-004: Fit component ranges on validation and clip test transforms [DECISION] Date: 2026-10-25 Status: active
Context: U, A, and C must be normalized without test leakage; U and A have score ranges dependent on each fitted model.
Options considered: Train-fitted ranges; validation-fitted ranges; or pooled train/validation ranges.
Decision and why: Fit min/max for U and A on validation predictions only, clip later transforms to [0,1], and use the bounded consequence value directly. Select thresholds from validation risk with NumPy linear percentile interpolation.
Consequences / how to reverse: Test values outside validation extrema saturate at 0/1. This follows the prompt's validation-only threshold/normalization rule. A different method needs an ADR and a logged sensitivity comparison.

## ADR-005: Keep the fixed policy after target discrepancies [DECISION] Date: 2026-10-25 Status: active
Context: Run raa-20261025-01 found full-policy accepted error 1.493% versus a ≈0.70% target; uncertainty-only selective accuracy exceeded full by 0.783 percentage points. The pooled synthetic-shift AUROC over all 12 variants was 0.731, while the 10-feature/2σ variant was 0.921.
Options considered: Change the fixed weights or threshold percentiles to match paper targets; report the logged values and sensitivity grid; or claim the paper target is reproduced from one selected stress variant.
Decision and why: Keep the prescribed 0.5/0.2/0.3 weights and 70/90 thresholds. Report all sensitivity and shift variants. Do not claim the full-policy error target is supported. Do not equate the pooled stress result to an unspecified paper recipe.
Consequences / how to reverse: The paper wording requires an author decision. See BLOCKERS.md. No parameter was tuned to a target.

## ADR-006: Define review workload as unweighted review cases [ASSUMPTION] Date: 2026-10-25 Status: active
Context: The prompt requests workload but provides no staff-time or cost model for Assisted versus Human Review.
Options considered: Invent weighted minutes/costs; or report separate level counts and an unweighted total.
Decision and why: Report Assisted and Human Review separately and define review workload as their sum in case counts/fraction. This is not a staff-time estimate.
Consequences / how to reverse: A real workflow cost model would require evidence and a superseding ADR.

## ADR-007: Bootstrap confidence intervals for stress variants by held-out case [DECISION] Date: 2026-10-25 Status: active
Context: Synthetic variants reuse the same held-out test cases. Independent resampling would treat repeated perturbations of one case as independent observations.
Options considered: Resample clean and shifted scores independently; or resample case IDs and retain all variants for each sampled ID.
Decision and why: Use a paired case bootstrap for each variant and for the pooled 12-variant AUROC. All perturbations belonging to a sampled test case stay together in each replicate.
Consequences / how to reverse: The paired interval is stored in stress_test.json/CSV. The test cases are still one split, and the interval does not quantify between-split variation; the exact paper recipe is unknown.

## ADR-008: Fix and record all experiment seeds [DECISION] Date: 2026-10-25 Status: active
Context: Reproducibility requires deterministic split, model, stress, and bootstrap randomness.
Options considered: Use fresh random seeds; or store a fixed contiguous split-seed range plus explicit component offsets and separate analysis seeds.
Decision and why: Use split seeds 2026–2055; validation split seed is the outer seed + 1; classifier, bootstrap members, and Isolation Forest use configured offsets; synthetic stress uses 4242; confidence intervals use 20261025.
Consequences / how to reverse: All seeds live in config.yaml or are derived as documented in code. Changing them requires a new run ID and should not overwrite a prior result.
