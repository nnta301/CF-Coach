"""Tests for the user-history processor."""

from __future__ import annotations

from typing import Any

from src.data.user_history import build_user_context


def make_submission(
    *,
    submission_id: int,
    verdict: str | None,
    contest_id: int | None,
    index: str,
    tags: list[str],
) -> dict[str, Any]:
    """Create one normalized submission record for testing."""
    return {
        "submission_id": submission_id,
        "creation_time_seconds": 1_700_000_000,
        "verdict": verdict,
        "problem": {
            "contest_id": contest_id,
            "index": index,
            "name": "Example Problem",
            "rating": 1700,
            "tags": tags,
        },
    }


def test_build_user_context_aggregates_unique_accepted_problems() -> None:
    profile = {"handle": "tourist", "rating": 3856}
    submissions = [
        make_submission(
            submission_id=1,
            verdict="OK",
            contest_id=4,
            index="A",
            tags=["math", "implementation"],
        ),
        make_submission(
            submission_id=2,
            verdict="OK",
            contest_id=4,
            index="A",
            tags=["math", "implementation"],
        ),
        make_submission(
            submission_id=3,
            verdict="OK",
            contest_id=71,
            index="A",
            tags=["implementation"],
        ),
        make_submission(
            submission_id=4,
            verdict="OK",
            contest_id=None,
            index="A",
            tags=["greedy"],
        ),
    ]

    context = build_user_context(profile, submissions)

    assert context == {
        "handle": "tourist",
        "rating": 3856,
        "solved_problem_ids": ["4-A", "71-A"],
        "tag_solve_counts": {
            "math": 1,
            "implementation": 2,
        },
    }


def test_accepted_submission_counts_after_an_earlier_failed_attempt() -> None:
    profile = {"handle": "tourist", "rating": 3856}
    submissions = [
        make_submission(
            submission_id=1,
            verdict="WRONG_ANSWER",
            contest_id=100,
            index="B",
            tags=["dp"],
        ),
        make_submission(
            submission_id=2,
            verdict="OK",
            contest_id=100,
            index="B",
            tags=["dp"],
        ),
    ]

    context = build_user_context(profile, submissions)

    assert context["solved_problem_ids"] == ["100-B"]
    assert context["tag_solve_counts"] == {"dp": 1}


def test_unrated_user_with_no_valid_solved_problems_has_empty_history() -> None:
    profile = {"handle": "new_user", "rating": None}
    submissions = [
        make_submission(
            submission_id=1,
            verdict="WRONG_ANSWER",
            contest_id=4,
            index="A",
            tags=["math"],
        ),
        make_submission(
            submission_id=2,
            verdict="OK",
            contest_id=None,
            index="A",
            tags=["greedy"],
        ),
    ]

    context = build_user_context(profile, submissions)

    assert context == {
        "handle": "new_user",
        "rating": None,
        "solved_problem_ids": [],
        "tag_solve_counts": {},
    }


def test_build_user_context_counts_duplicate_tags_once_per_problem() -> None:
    profile = {"handle": "tourist", "rating": 3856}
    submissions = [
        make_submission(
            submission_id=1,
            verdict="OK",
            contest_id=4,
            index="A",
            tags=["math", "math", "implementation"],
        ),
    ]

    context = build_user_context(profile, submissions)

    assert context["tag_solve_counts"] == {
        "math": 1,
        "implementation": 1,
    }
