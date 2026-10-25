# Conventions

- Python 3.11+, type hints, module and public-function docstrings.
- Use structured logging rather than `print` in application/library code.
- Keep model parameters, seeds, weights, and thresholds in `config.yaml`.
- Every reported number must link to a command and actual run output; otherwise label it `NOT RUN`.
- Never fit preprocessing, models, normalizers, or thresholds on the held-out test partition.
- Preserve the three policy levels: Automatic, Assisted, Human Review.
- Explanations are deterministic templates and cannot mutate predictions or routing.
- Claims must include the prototype, non-clinical limitation and all honesty constraints in `AGENTS.md`.
- Intended commit format: `[<TASK-ID>] <what>`.
