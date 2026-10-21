"""Verify the live Sprint 1 end-to-end flow and solved-problem exclusion."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import Any

from src.data.codeforces_client import CodeforcesClient, CodeforcesClientError
from src.data.problem_catalog import fetch_problem_catalog
from src.data.user_history import build_user_context
from src.recommender.baseline import recommend

DEFAULT_HANDLES = ("tourist", "Petr", "Benq")


def _expected_recommendation_count(
    user_context: dict[str, Any],
    problems: list[dict[str, Any]],
) -> int:
    """Return the capped count of unique, rated, unsolved candidates."""
    solved_problem_ids = set(user_context["solved_problem_ids"])
    seen_problem_ids: set[str] = set()
    eligible_count = 0

    for problem in problems:
        problem_id = problem["problem_id"]
        if (
            problem_id in solved_problem_ids
            or problem_id in seen_problem_ids
            or problem["rating"] is None
        ):
            continue
        seen_problem_ids.add(problem_id)
        eligible_count += 1

    return min(10, eligible_count)


def verify_handles(
    handles: Sequence[str],
    *,
    client: CodeforcesClient | None = None,
) -> list[dict[str, Any]]:
    """Return recommendation counts and solved overlaps for live-flow handles."""
    api = client if client is not None else CodeforcesClient()
    problems = fetch_problem_catalog(api)
    results: list[dict[str, Any]] = []

    for handle in handles:
        profile = api.get_user_profile(handle)
        user_context = build_user_context(
            profile,
            api.get_user_submissions(profile["handle"]),
        )
        recommendations = recommend(user_context, problems)
        recommendation_ids = [item["problem_id"] for item in recommendations]
        recommended_ids = set(recommendation_ids)
        solved_overlap = sorted(
            recommended_ids.intersection(user_context["solved_problem_ids"])
        )
        seen_recommendation_ids: set[str] = set()
        duplicate_recommendation_ids: set[str] = set()
        for problem_id in recommendation_ids:
            if problem_id in seen_recommendation_ids:
                duplicate_recommendation_ids.add(problem_id)
            seen_recommendation_ids.add(problem_id)
        results.append(
            {
                "handle": profile["handle"],
                "recommendation_count": len(recommendations),
                "expected_recommendation_count": _expected_recommendation_count(
                    user_context,
                    problems,
                ),
                "solved_overlap": solved_overlap,
                "duplicate_recommendation_ids": sorted(duplicate_recommendation_ids),
            }
        )

    return results


def main(argv: Sequence[str] | None = None) -> int:
    """Print reproducible live end-to-end verification results and an exit status."""
    parser = argparse.ArgumentParser(
        description="Verify that live recommendations exclude solved Codeforces problems."
    )
    parser.add_argument(
        "handles",
        nargs="*",
        default=DEFAULT_HANDLES,
        help="Codeforces handles to verify (default: tourist Petr Benq)",
    )
    args = parser.parse_args(argv)

    try:
        results = verify_handles(args.handles)
    except (CodeforcesClientError, ValueError) as error:
        print(f"Could not run live-flow verification: {error}", file=sys.stderr)
        return 1

    valid = True
    for result in results:
        overlap = result["solved_overlap"]
        duplicate_ids = result["duplicate_recommendation_ids"]
        print(
            f"{result['handle']}: {result['recommendation_count']} recommendations "
            f"(expected {result['expected_recommendation_count']}); solved overlap: "
            f"{len(overlap)}; duplicate IDs: {len(duplicate_ids)}"
        )
        if (
            result["recommendation_count"] == 0
            or result["recommendation_count"] != result["expected_recommendation_count"]
            or overlap
            or duplicate_ids
        ):
            valid = False

    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
