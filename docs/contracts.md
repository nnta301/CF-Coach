# Data Contracts

These contracts are the shared interface between modules. Keep external boundaries JSON-serializable.

## ProblemId

- Format: `<contest_id>-<index>`
- Example: `123-A`

## UserContext

```json
{
  "handle": "tourist",
  "rating": 1800,
  "solved_problem_ids": ["4-A", "71-A", "158-A"],
  "tag_solve_counts": {
    "implementation": 12,
    "dp": 2,
    "graphs": 1
  }
}
```

- `solved_problem_ids` is a list at the module/API boundary. A recommender may convert it to a set internally.
- `rating` may be `null` for unrated users; callers must handle this explicitly.

## Problem

```json
{
  "problem_id": "123-A",
  "name": "Example Problem",
  "rating": 1700,
  "tags": ["dp", "greedy"],
  "url": "https://codeforces.com/problemset/problem/123/A"
}
```

## RecommendationItem

```json
{
  "problem_id": "123-A",
  "name": "Example Problem",
  "rating": 1700,
  "tags": ["dp", "greedy"],
  "url": "https://codeforces.com/problemset/problem/123/A",
  "score": 0.82,
  "reason": "Rating is close to your level and DP is under-practiced."
}
```

## Contract change procedure

1. Propose the change in the affected GitHub Issue.
2. Describe why it is needed and which modules are affected.
3. Obtain agreement in the Issue.
4. Update this document and implementation in linked PRs.
