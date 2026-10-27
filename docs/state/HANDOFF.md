# HANDOFF

Updated: 2026-10-27 | Session #: 4 | Current task: P4.1j review capacity | Status: Modes A-D complete; replacement demo in progress.

## Do next

1. Persist the seed-42 validation risk distribution under results/demo and bump/validate the artifact version.
2. Map total review capacity to validation percentiles so the default 30 referrals per 100 preserves automatic p70 / human-review p90.
3. Add capacity API and UI tests, and confirm reported results remain read-only.

## Current state

- Active repository: D:\ERA CP; latest task commit is [P4.1i] Add live what-if controls.
- P4.1a-i complete. Modes A-D are functional: examples, six-field guided entry, strict in-memory CSV batch, and live four-slider what-if.
- Synthetic stress helper follows config.yaml signed 3-sigma/eight-feature recipe, uses the saved train-fitted scaler standard deviations, clips negatives, and labels output synthetic.
- Verification: inference 5 passed; example 2 passed; batch/UI 5 passed; what-if/stress 5 passed. The UI test confirms moving a slider changes risk.
- Artifact remains version 1 in results/demo; capacity task will add persisted validation risks and bump it.
- Why abstain page loads canonical metrics.json but should be checked and expanded. Full UI/privacy test matrix and README remain.
- GNU Make 3.82.90 and CLAIM-001 remain open.

## WIP files

- README.md remains uncommitted and needs final demo usage/screenshot/viva content.
- streamlit_app.py contains working modes A-D; capacity UI is not yet wired.

## Next 3 commands/actions

- Save validation risk data and regenerate model_bundle artifact.
- Implement default-preserving capacity threshold mapping and reroute display.
- Test capacity at default and changed values; update P4.1j state and commit.
