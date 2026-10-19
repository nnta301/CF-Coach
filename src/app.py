"""Minimal recommendation CLI: python -m src.app HANDLE."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from src.data.codeforces_client import CodeforcesClient, CodeforcesClientError
from src.data.problem_catalog import fetch_problem_catalog
from src.data.user_history import build_user_context
from src.recommender.baseline import recommend


def main(
    argv: Sequence[str] | None = None,
    *,
    client: CodeforcesClient | None = None,
) -> int:
    """Fetch a handle's data and display ten recommendations when available."""
    parser = argparse.ArgumentParser(
        description="Recommend 10 unsolved Codeforces problems for your handle."
    )
    parser.add_argument("handle", help="Your Codeforces handle")
    args = parser.parse_args(argv)
    api = client if client is not None else CodeforcesClient()

    try:
        profile = api.get_user_profile(args.handle)
        submissions = api.get_user_submissions(profile["handle"])
        user_context = build_user_context(profile, submissions)
        problems = fetch_problem_catalog(api)
        recommendations = recommend(user_context, problems)
    except (CodeforcesClientError, ValueError) as error:
        print(f"Could not load recommendations: {error}", file=sys.stderr)
        return 1

    rating_label = "unrated" if profile["rating"] is None else str(profile["rating"])
    print(f"Recommendations for {profile['handle']} (rating: {rating_label})")
    if not recommendations:
        print("No rated, unsolved problems are available.")
        return 0

    if len(recommendations) < 10:
        print(
            f"Only {len(recommendations)} rated, unsolved problems are available "
            "(requested 10)."
        )
    else:
        print("Showing 10 recommendations.")

    for position, item in enumerate(recommendations, start=1):
        tags = ", ".join(item["tags"]) or "(none)"
        print(f"\n{position}. {item['name']} [{item['problem_id']}]")
        print(f"   Rating: {item['rating']} | Tags: {tags}")
        print(f"   URL: {item['url']}")
        print(f"   Reason: {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
