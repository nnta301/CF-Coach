"""Integration tests for the reproducible live-demo verification command."""

from typing import Any

from scripts.verify_live_demo import verify_handles
from tests.test_codeforces_client import FakeResponse, FakeSession, make_client


def raw_problem(number: int) -> dict[str, Any]:
    return {
        "contestId": number,
        "index": "A",
        "name": f"Problem {number}",
        "rating": 1600,
        "tags": ["dp"],
    }


def raw_submission(number: int) -> dict[str, Any]:
    return {
        "id": number,
        "creationTimeSeconds": 1_700_000_000,
        "verdict": "OK",
        "problem": raw_problem(number),
    }


def test_verify_handles_checks_solved_overlap_using_shared_catalog() -> None:
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

    results = verify_handles(["first", "second"], client=make_client(session))

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
