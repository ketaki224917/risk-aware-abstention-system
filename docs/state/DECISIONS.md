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
