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
        recommended_ids = {item["problem_id"] for item in recommendations}
        solved_overlap = sorted(
            recommended_ids.intersection(user_context["solved_problem_ids"])
        )
        results.append(
            {
                "handle": profile["handle"],
                "recommendation_count": len(recommendations),
                "solved_overlap": solved_overlap,
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
        print(
            f"{result['handle']}: {result['recommendation_count']} recommendations; "
            f"solved overlap: {len(overlap)}"
        )
        if result["recommendation_count"] == 0 or overlap:
            valid = False

    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
