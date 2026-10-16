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