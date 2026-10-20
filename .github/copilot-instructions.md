# Copilot Review Instructions

Prioritize high-confidence correctness, security, reliability, and maintainability findings.
Avoid minor style comments unless they hide a meaningful defect.

- Keep public module boundaries compatible with `docs/contracts.md`.
- At Codeforces API boundaries, check normalized data, caching, and error handling.
- Ensure duplicate handling and data processing are deterministic.
- Prevent future-information leakage in data processing and ML experiments.
- Treat unattempted problems as unknown, not confirmed failures.
- Prefer reproducible experiments, meaningful tests, and documentation updates for public behavior changes.
- Do not claim test results that were not verified.
- Do not invent Codeforces API behavior or undocumented assumptions.
- Add path-specific instructions only when a concrete need has appeared; do not add them preemptively.

## Issue, documentation, and contract review

- When a pull request links a GitHub Issue, inspect the Issue's goal, scope, out-of-scope items, acceptance criteria, dependencies, and relevant discussion.
- For a linked Issue, compare the pull request diff against every acceptance criterion. Report a missing requirement, missing evidence, or scope mismatch when found.
- If the linked Issue, its criteria, or supporting evidence are unavailable, identify that limitation and do not claim that the Issue is complete.
- Assess `README.md`, `docs/architecture.md`, `docs/contracts.md`, and the active sprint documentation for staleness on every change. Review and update each affected document; a document may remain unchanged when the assessment shows that it is genuinely unaffected. Also review other documentation that is plausibly affected, including `docs/workflow.md`.
- When public or module boundaries change, compare the implementation with `docs/contracts.md`, including field names, types, nullability, ordering, duplicate handling, error behavior, and JSON-serializability where applicable.
- When a documented contract changes, require focused tests that demonstrate the changed behavior. Name the relevant contract section and missing test evidence in any finding.
- Do not require unrelated documentation changes, unrelated refactoring, or speculative tests.