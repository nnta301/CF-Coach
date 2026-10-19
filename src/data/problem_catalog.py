"""Fetch a rated problem catalog matching the shared Problem contract."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from src.data.codeforces_client import CodeforcesClient, CodeforcesResponseError


def fetch_problem_catalog(client: CodeforcesClient) -> list[dict[str, Any]]:
    """Normalize unique problems; omit entries without a contest ID or rating.

    Keep the first occurrence of each problem ID in API order. Invalid field
    types raise an API response error rather than silently returning partial data.
    """
    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()

    for problem in client.get_problemset():
        if not isinstance(problem, dict):
            raise CodeforcesResponseError("Invalid catalog problem format.")

        contest_id = problem.get("contestId")
        rating = problem.get("rating")
        if contest_id is None or rating is None:
            continue
        if type(contest_id) is not int or contest_id <= 0:
            raise CodeforcesResponseError("Catalog contest id has an invalid format.")
        if type(rating) is not int or rating <= 0:
            raise CodeforcesResponseError("Catalog rating has an invalid format.")

        index = problem.get("index")
        name = problem.get("name")
        tags = problem.get("tags", [])
        if not isinstance(index, str) or not index.strip():
            raise CodeforcesResponseError(
                "Catalog problem index has an invalid format."
            )
        if not isinstance(name, str) or not name.strip():
            raise CodeforcesResponseError("Catalog problem name has an invalid format.")
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise CodeforcesResponseError(
                "Catalog problem tags have an invalid format."
            )

        problem_id = f"{contest_id}-{index}"
        if problem_id in seen:
            continue
        seen.add(problem_id)
        catalog.append(
            {
                "problem_id": problem_id,
                "name": name,
                "rating": rating,
                "tags": list(dict.fromkeys(tags)),
                "url": (
                    "https://codeforces.com/problemset/problem/"
                    f"{contest_id}/{quote(index, safe='')}"
                ),
            }
        )

    return catalog
