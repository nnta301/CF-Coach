"""Behavioral tests for candidate filtering and baseline ranking."""

import json
from copy import deepcopy
from typing import Any

import pytest

from src.recommender.baseline import recommend


def context(**overrides: Any) -> dict[str, Any]:
    return {
        "handle": "example",
        "rating": 1600,
        "solved_problem_ids": [],
        "tag_solve_counts": {},
        **overrides,
    }


def problem(number: int, rating: int | None = 1600, **overrides: Any) -> dict[str, Any]:
    return {
        "problem_id": f"{number}-A",
        "name": f"Problem {number}",
        "rating": rating,
        "tags": ["dp"],
        "url": f"https://codeforces.com/problemset/problem/{number}/A",
        **overrides,
    }


def test_returns_ten_unique_unsolved_ranked_contract_records() -> None:
    catalog = [problem(i, 800 + 100 * i) for i in range(1, 20)]
    catalog += [problem(1)]
    user = context(solved_problem_ids=["2-A", "3-A", "4-A"])

    results = recommend(user, catalog)

    assert len(results) == 10
    ids = [item["problem_id"] for item in results]
    assert len(set(ids)) == 10
    assert not set(ids) & set(user["solved_problem_ids"])
    assert [item["score"] for item in results] == sorted(
        [item["score"] for item in results], reverse=True
    )
    assert all(
        set(item) == {"problem_id", "name", "rating", "tags", "url", "score", "reason"}
        and isinstance(item["score"], float)
        and item["reason"]
        for item in results
    )
    assert json.loads(json.dumps(results)) == results


def test_prefers_close_rating_when_tag_practice_is_equal() -> None:
    results = recommend(
        context(), [problem(1, 800), problem(2, 1600), problem(3, 1700)]
    )
    assert [item["problem_id"] for item in results] == ["2-A", "3-A", "1-A"]


def test_boosts_under_practiced_and_unseen_tags_at_equal_rating() -> None:
    user = context(tag_solve_counts={"math": 20, "dp": 2})
    results = recommend(
        user,
        [
            problem(1, tags=["math"]),
            problem(2, tags=["dp"]),
            problem(3, tags=["graphs"]),
        ],
    )
    assert [item["problem_id"] for item in results] == ["3-A", "2-A", "1-A"]
    assert "graphs (0 solved" in results[0]["reason"]
    assert "dp (2 solved" in results[1]["reason"]


def test_tag_boost_does_not_outweigh_a_large_rating_gap() -> None:
    results = recommend(
        context(tag_solve_counts={"math": 100}),
        [problem(1, 3200, tags=["graphs"]), problem(2, 1600, tags=["math"])],
    )
    assert results[0]["problem_id"] == "2-A"


def test_unrated_user_uses_and_explains_starting_rating() -> None:
    results = recommend(context(rating=None), [problem(1, 1600), problem(2, 800)])
    assert results[0]["problem_id"] == "2-A"
    assert "Unrated user: using starting rating 800" in results[0]["reason"]


def test_handles_untagged_and_unrated_problems() -> None:
    results = recommend(context(), [problem(1, tags=[]), problem(2, rating=None)])
    assert len(results) == 1
    assert results[0]["problem_id"] == "1-A"
    assert results[0]["score"] == pytest.approx(0.8)
    assert "No tags available" in results[0]["reason"]


def test_ties_are_deterministic_independent_of_catalog_order() -> None:
    catalog = [problem(3), problem(1), problem(2)]
    expected = recommend(context(), catalog)
    assert recommend(context(), list(reversed(catalog))) == expected
    assert [item["problem_id"] for item in expected] == ["1-A", "2-A", "3-A"]


def test_returns_available_candidates_when_fewer_than_ten() -> None:
    assert recommend(context(), []) == []
    assert recommend(context(solved_problem_ids=["1-A"]), [problem(1)]) == []
    assert len(recommend(context(), [problem(1), problem(2)])) == 2


def test_custom_limit() -> None:
    assert len(recommend(context(), [problem(i) for i in range(20)], limit=12)) == 12


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "10"])
def test_rejects_invalid_limit(limit: Any) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        recommend(context(), [problem(1)], limit=limit)


def test_does_not_mutate_inputs_or_share_output_tag_lists() -> None:
    user = context()
    catalog = [problem(1, tags=["dp", "dp", "math"])]
    before = deepcopy((user, catalog))
    result = recommend(user, catalog)
    assert (user, catalog) == before
    assert result[0]["tags"] == ["dp", "math"]
    result[0]["tags"].append("graphs")
    assert (user, catalog) == before
