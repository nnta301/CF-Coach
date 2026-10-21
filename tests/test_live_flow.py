"""Integration tests for the reproducible live-flow verification command."""

from typing import Any

import pytest

import scripts.verify_live_flow as live_flow
from src.recommender.baseline import recommend as baseline_recommend
from tests.test_codeforces_client import FakeResponse, FakeSession, make_client


def raw_problem(number: int) -> dict[str, Any]:
    """Return one raw catalog problem matching the Codeforces API shape."""
    return {
        "contestId": number,
        "index": "A",
        "name": f"Problem {number}",
        "rating": 1600,
        "tags": ["dp"],
    }


def raw_submission(number: int) -> dict[str, Any]:
    """Return one accepted raw submission for the matching catalog problem."""
    return {
        "id": number,
        "creationTimeSeconds": 1_700_000_000,
        "verdict": "OK",
        "problem": raw_problem(number),
    }


class DemoClient:
    """Provide deterministic catalog and history data without network access."""

    def __init__(
        self, problems: list[dict[str, Any]], solved_numbers: list[int]
    ) -> None:
        self._problems = problems
        self._solved_numbers = solved_numbers

    def get_problemset(self) -> list[dict[str, Any]]:
        """Return the configured raw problem catalog."""
        return self._problems

    def get_user_profile(self, handle: str) -> dict[str, Any]:
        """Return a fixed rated profile for the requested handle."""
        return {"handle": handle, "rating": 1600}

    def get_user_submissions(self, handle: str) -> list[dict[str, Any]]:
        """Return accepted submissions for configured solved problem numbers."""
        return [raw_submission(number) for number in self._solved_numbers]


def verification_result(
    *,
    recommendation_count: int,
    expected_recommendation_count: int,
    solved_overlap: list[str] | None = None,
    duplicate_recommendation_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build one verifier result record for main-command tests."""
    return {
        "handle": "First",
        "recommendation_count": recommendation_count,
        "expected_recommendation_count": expected_recommendation_count,
        "solved_overlap": solved_overlap or [],
        "duplicate_recommendation_ids": duplicate_recommendation_ids or [],
    }


def test_verify_handles_checks_solved_overlap_using_shared_catalog() -> None:
    """Verify cross-module solved exclusion while fetching the catalog once."""
    session = FakeSession(
        [
            FakeResponse(
                {
                    "status": "OK",
                    "result": {
                        "problems": [raw_problem(number) for number in range(1, 12)]
                    },
                }
            ),
            FakeResponse(
                {"status": "OK", "result": [{"handle": "First", "rating": 1600}]}
            ),
            FakeResponse({"status": "OK", "result": [raw_submission(1)]}),
            FakeResponse(
                {"status": "OK", "result": [{"handle": "Second", "rating": 1600}]}
            ),
            FakeResponse({"status": "OK", "result": [raw_submission(2)]}),
        ]
    )

    results = live_flow.verify_handles(["first", "second"], client=make_client(session))

    assert results == [
        verification_result(recommendation_count=10, expected_recommendation_count=10)
        | {"handle": "First"},
        verification_result(recommendation_count=10, expected_recommendation_count=10)
        | {"handle": "Second"},
    ]
    assert [call["url"].rsplit("/", 1)[-1] for call in session.calls] == [
        "problemset.problems",
        "user.info",
        "user.status",
        "user.info",
        "user.status",
    ]


def test_main_returns_zero_for_recommendations_without_solved_overlap(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify the command succeeds only when every handle has safe results."""
    monkeypatch.setattr(
        live_flow,
        "verify_handles",
        lambda handles: [
            verification_result(
                recommendation_count=10, expected_recommendation_count=10
            ),
            verification_result(recommendation_count=1, expected_recommendation_count=1)
            | {"handle": "Second"},
        ],
    )

    assert live_flow.main(["first", "second"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "First: 10 recommendations (expected 10); solved overlap: 0; duplicate IDs: 0",
        "Second: 1 recommendations (expected 1); solved overlap: 0; duplicate IDs: 0",
    ]


def test_main_returns_one_when_a_handle_has_no_recommendations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify an empty recommendation result produces the documented failure status."""
    monkeypatch.setattr(
        live_flow,
        "verify_handles",
        lambda handles: [
            verification_result(recommendation_count=0, expected_recommendation_count=0)
        ],
    )

    assert live_flow.main(["first"]) == 1


def test_main_returns_one_when_a_recommendation_is_solved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify a solved-problem overlap produces the documented failure status."""
    monkeypatch.setattr(
        live_flow,
        "verify_handles",
        lambda handles: [
            verification_result(
                recommendation_count=10,
                expected_recommendation_count=10,
                solved_overlap=["1-A"],
            )
        ],
    )

    assert live_flow.main(["first"]) == 1


def test_main_rejects_incomplete_recommendations_when_ten_are_expected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproduce the issue scenario with twelve eligible candidates and one result."""
    monkeypatch.setattr(
        live_flow,
        "CodeforcesClient",
        lambda: DemoClient([raw_problem(number) for number in range(1, 13)], []),
    )
    monkeypatch.setattr(
        live_flow,
        "recommend",
        lambda user_context, problems: baseline_recommend(
            user_context, problems, limit=1
        ),
    )

    assert live_flow.main(["example"]) == 1


def test_main_accepts_all_eligible_recommendations_below_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify all candidates are required when fewer than ten are eligible."""
    monkeypatch.setattr(
        live_flow,
        "CodeforcesClient",
        lambda: DemoClient([raw_problem(number) for number in range(1, 4)], []),
    )

    assert live_flow.main(["example"]) == 0


def test_main_rejects_duplicate_recommendation_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify repeated recommendation IDs produce a failed verification status."""
    monkeypatch.setattr(
        live_flow,
        "CodeforcesClient",
        lambda: DemoClient([raw_problem(number) for number in range(1, 3)], []),
    )
    monkeypatch.setattr(
        live_flow,
        "recommend",
        lambda user_context, problems: [problems[0], problems[0]],
    )

    assert live_flow.main(["example"]) == 1


def test_expected_recommendation_count_ignores_duplicate_unrated_and_solved_problems() -> (
    None
):
    """Verify candidate counting matches the verifier's eligibility rules."""
    user_context = {"solved_problem_ids": ["4-A"]}
    problems = [
        {"problem_id": "1-A", "rating": 1600},
        {"problem_id": "1-A", "rating": 1600},
        {"problem_id": "2-A", "rating": None},
        {"problem_id": "3-A", "rating": 1600},
        {"problem_id": "4-A", "rating": 1600},
    ]

    assert live_flow._expected_recommendation_count(user_context, problems) == 2
