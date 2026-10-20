"""Utilities for building a user context from Codeforces history."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_user_context(
    profile: dict[str, str | int | None],
    submissions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a normalized UserContext from profile and submissions."""
    solved_problem_ids: list[str] = []
    seen_problem_ids: set[str] = set()
    tag_solve_counts: Counter[str] = Counter()

    for submission in submissions:
        if submission["verdict"] != "OK":
            continue

        problem = submission["problem"]
        contest_id = problem["contest_id"]

        if contest_id is None:
            continue

        problem_id = f"{contest_id}-{problem['index']}"

        if problem_id in seen_problem_ids:
            continue

        seen_problem_ids.add(problem_id)
        solved_problem_ids.append(problem_id)
        unique_tags = list(dict.fromkeys(problem["tags"]))
        tag_solve_counts.update(unique_tags)

    return {
        "handle": profile["handle"],
        "rating": profile["rating"],
        "solved_problem_ids": solved_problem_ids,
        "tag_solve_counts": dict(tag_solve_counts),
    }
