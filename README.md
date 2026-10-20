# CF-Coach

CF-Coach is a personalized Codeforces problem recommender for competitive programmers.

## Current status

Current sprint: [Sprint 1](docs/sprints/sprint-01.md)

Problem catalog, baseline recommender, and CLI implementations are available on the Sprint 1 feature branches and are pending teammate review and merge.

## Documentation

- [Proposal](docs/proposal.md)
- [Architecture](docs/architecture.md)
- [Data contracts](docs/contracts.md)
- [Team workflow](docs/workflow.md)
- [Sprint history](docs/sprints/README.md)

## Prerequisites

- Python 3.11 or newer
- pip
- Git

## Local setup

### macOS/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Run tests

With the virtual environment activated:

```bash
pytest
ruff check .
ruff format --check .
```

## Codeforces API client

```python
from src.data.codeforces_client import CodeforcesClient
from src.data.user_history import build_user_context

client = CodeforcesClient()

profile = client.get_user_profile("tourist")
submissions = client.get_user_submissions(profile["handle"])
user_context = build_user_context(profile, submissions)

print(user_context)
```

- `get_user_profile()` returns the canonical handle and current rating. The rating is `None` for unrated users.
- `get_user_submissions()` returns normalized submission records without filtering by verdict. Solved-problem extraction and tag aggregation are handled by the user-history processor.
- `build_user_context()` derives unique solved problem IDs and tag solve counts from accepted submissions with a valid contest ID.
- The client raises `CodeforcesUserNotFoundError` for a non-existent handle and `CodeforcesClientError` for network or Codeforces API failures.

## Problem catalog

```python
from src.data.codeforces_client import CodeforcesClient
from src.data.problem_catalog import fetch_problem_catalog

problems = fetch_problem_catalog(CodeforcesClient())
print(problems[:3])
```

- Fetches the public `problemset.problems` endpoint using the existing client's timeout, request pacing, and error handling.
- Returns unique `Problem` records matching [the shared contract](docs/contracts.md), with IDs such as `123-A` and public problem URLs.
- Skips problems with a missing/null rating or contest ID; no rating is guessed. An empty catalog returns an empty list.
- Preserves API order, keeps the first occurrence of a duplicate problem ID, and removes repeated tags.
- Malformed records raise `CodeforcesResponseError`; network/API failures are propagated rather than returned as an empty catalog.

## Baseline recommendations

```python
from src.recommender.baseline import recommend

# user_context and problems come from the data examples above.
recommendations = recommend(user_context, problems, limit=10)
```

- Accepts the shared `UserContext` and normalized `Problem` records and returns JSON-serializable `RecommendationItem` records.
- Excludes solved problems, duplicate IDs, and problems with null ratings. Returns 10 results by default when enough candidates exist, otherwise all available candidates; it never pads with solved or repeated problems.
- Uses `score = 0.8 / (1 + abs(problem_rating - target_rating) / 400) + 0.2 * tag_boost`, where `tag_boost` is the mean of `1 / (1 + solved_count)` over the problem's unique tags. An unseen tag has count zero; an untagged problem receives no tag boost. These weights are a transparent Sprint 1 heuristic, not a learned model.
- Uses rating 800 for an unrated user and explicitly states that fallback in each reason. Otherwise the target is the user's current rating.
- Every reason states rating distance and the least-practiced tag's solved count, when tags exist. Ties use smaller rating distance, then lexicographic problem ID for repeatable ordering.

## Recommendation CLI

From the repository root, with the virtual environment activated:

```bash
python -m src.app tourist
python -m src.app --help
```

The CLI fetches the user's profile, submission history, and problem catalog, then displays 10 unsolved recommendations with name, rating, tags, URL, and reason. It uses the canonical handle returned by Codeforces. Unrated users see the starting-rating fallback in each reason.

If fewer than 10 eligible problems exist, it shows all available results and explains the shortfall. An empty result is reported explicitly. Invalid/blank handles and API/network failures produce a readable message on stderr and exit status 1; argument usage errors use exit status 2. Successful output, including an empty result, uses exit status 0.

This command needs internet access and makes three paced Codeforces API requests. It does not cache responses. Tests use fake HTTP responses and do not contact Codeforces.
