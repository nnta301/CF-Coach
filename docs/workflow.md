# Team Workflow

## Project board

Use a GitHub Project board with these columns:

1. Backlog
2. Todo
3. In Progress
4. Blocked
5. In Review
6. Done

Every card must correspond to a GitHub Issue.

## Sprint cadence

- Sprint length: one week.
- Sprint planning: choose only the highest-priority ready issues.
- Mid-sprint checkpoint: identify blocked dependencies early.
- Sprint review: demo the working result, record what was completed, and revise the backlog before planning the next sprint.

## Issue rules

- One primary owner per issue.
- Each issue has acceptance criteria and a small, testable scope.
- Add dependencies explicitly, e.g. `Blocked by #12`.
- If blocked for more than one focused work session, post a comment describing: what was tried, observed result, and decision needed.

## Pull request rules

- Do not push directly to `main`.
- One logical change per branch and PR.
- Use `Closes #<issue-number>` in the PR description.
- The other teammate reviews before merge.
- A bug is recorded as a GitHub Issue with reproduction steps, expected result, actual result, and evidence.
- GitHub Actions runs `pytest`, `ruff check .`, and `ruff format --check .` for pull requests targeting `main` and pushes to `main`.
- CI installs dependencies from the committed `requirements-dev.lock`. Update the lock intentionally when dependency requirements change.

## Manual CodeRabbit reviews

Use CodeRabbit for an on-demand pull-request review when GitHub Copilot review quota is exhausted.

Repository configuration lives in `.coderabbit.yaml`. Automatic reviews are disabled. Review guidelines remain in `.github/copilot-instructions.md` and apply to all reviewed files.

Post these commands as separate top-level comments on the pull request:

- `@coderabbitai review` — request an incremental review.
- `@coderabbitai full review` — request a fresh review of the entire pull request.

After pushing fixes, request another review manually when needed.

Review availability depends on the account's current plan and usage limits. Record any restriction that prevents verification.

The author must assess feedback and verify changes. CodeRabbit feedback does not replace the teammate review required before merge.

## Shared environment

- Each developer creates their own local Python 3.11 `.venv`.
- Never commit `.venv` or `.env`.
- Before opening a PR, run `pytest`, `ruff check .`, and `ruff format --check .`.
