# Sprint 1 — Data-to-Recommendation Spike

## Status

Active. This record should be completed during the Sprint 1 review.

## Goal

Given a Codeforces handle, return 10 unsolved problems using a transparent baseline based on rating proximity and under-practiced tags.

## Prerequisite

The shared Python development environment is established in PR #1. It is a Sprint 1 prerequisite, not a separate Sprint Issue.

## Planned issues

| Issue | Owner | Purpose |
|---|---|---|
| #2 | nnta301 | Codeforces API client: profile and submissions |
| #3 | nnta301 | User-history processor |
| #4 | nnta301 | Data-pipeline tests and sample output |
| #5 | nguyenphongg233 | Normalized Codeforces problem catalog |
| #6 | nguyenphongg233 | Candidate filter and baseline scorer |
| #7 | nguyenphongg233 | Minimal recommendation output |
| #8 | nnta301 | End-to-end integration and demo |

## Definition of success

- The full flow works for at least three real Codeforces handles.
- The system returns 10 recommendations when candidates are available.
- No solved problem is returned.
- Every recommendation has title, rating, tags, URL, and a short reason.

## Results

_To be completed at the end of the sprint._

### Completed

- None yet.

### Not completed / carried over

- None yet.

### Evidence

- Pull requests:
  - #5 problem catalog: [PR #17](https://github.com/nnta301/CF-Coach/pull/17), pending teammate review and merge.
  - #6 baseline recommender: [PR #18](https://github.com/nnta301/CF-Coach/pull/18), draft depending on PR #17.
- #7 CLI implementation is on `feat/7-recommendation-cli`, depending on PR #18; teammate review and merge remain pending.
- Demo/test results:
  - The combined #5–#7 implementation passed 60 local pytest tests and `ruff check .`. CLI tests cover raw fake API responses through display, invalid handles, unrated users, and insufficient candidates.
  - `python -m src.app tourist` successfully displayed 10 recommendations using the live Codeforces API on 19 Oct 2026. The full three-handle demo remains part of #8.

## Retrospective

_To be completed during the sprint review._

### What went well

-

### What was blocked or difficult

-

### Change for Sprint 2

-
