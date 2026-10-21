"""Integration tests for the reproducible live-flow verification command."""

from typing import Any

import pytest

import scripts.verify_live_flow as live_flow
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
        {"handle": "First", "recommendation_count": 10, "solved_overlap": []},
        {"handle": "Second", "recommendation_count": 10, "solved_overlap": []},
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
            {"handle": "First", "recommendation_count": 10, "solved_overlap": []},
            {"handle": "Second", "recommendation_count": 1, "solved_overlap": []},
        ],
    )

    assert live_flow.main(["first", "second"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "First: 10 recommendations; solved overlap: 0",
        "Second: 1 recommendations; solved overlap: 0",
    ]


def test_main_returns_one_when_a_handle_has_no_recommendations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify an empty recommendation result produces the documented failure status."""
    monkeypatch.setattr(
        live_flow,
        "verify_handles",
        lambda handles: [
            {"handle": "First", "recommendation_count": 0, "solved_overlap": []}
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
            {
                "handle": "First",
                "recommendation_count": 10,
                "solved_overlap": ["1-A"],
            }
        ],
    )

    assert live_flow.main(["first"]) == 1
