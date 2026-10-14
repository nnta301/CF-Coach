# Architecture

## Sprint 1 data flow

```text
Codeforces API
  ├── profile + submissions ──> User-history processor ──> UserContext
  └── problemset catalog ────────────────────────────────> Problem catalog
UserContext + Problem catalog ──> Baseline recommender ──> RecommendationItem[]
                                                        └──> CLI / minimal UI
```

## Modules

| Module | Responsibility |
|---|---|
| `src/data/codeforces_client.py` | Calls Codeforces API and normalizes raw responses. |
| `src/data/user_history.py` | Derives solved IDs and tag practice statistics. |
| `src/data/problem_catalog.py` | Produces normalized problem records. |
| `src/recommender/baseline.py` | Filters candidates and ranks recommendations. |
| `src/app.py` | Accepts a handle and renders recommendation results. |

## Working rule

Modules communicate only through the contracts in [contracts.md](contracts.md). Any incompatible change must be proposed in the related GitHub Issue before implementation.
