"""CLI integration tests using deterministic raw Codeforces responses."""

from typing import Any

import pytest
import requests

from src.app import main
from tests.test_codeforces_client import FakeResponse, FakeSession, make_client


def api_problem(number: int) -> dict[str, Any]:
    return {
        "contestId": number,
        "index": "A",
        "name": f"Example Problem {number}",
        "rating": 1600,
        "tags": ["dp", "greedy"],
    }


def cli_session(
    *,
    rating: int | None = 1600,
    count: int = 14,
    solved: bool = True,
) -> FakeSession:
    submissions = (
        [
            {
                "id": 1,
                "creationTimeSeconds": 1_700_000_000,
                "verdict": "OK",
                "problem": api_problem(1),
            }
        ]
        if solved
        else []
    )
    return FakeSession(
        [
            FakeResponse(
                {"status": "OK", "result": [{"handle": "Canonical", "rating": rating}]}
            ),
            FakeResponse({"status": "OK", "result": submissions}),
            FakeResponse(
                {
                    "status": "OK",
                    "result": {
                        "problems": [api_problem(i) for i in range(1, count + 1)]
                    },
                }
            ),
        ]
    )


def test_cli_displays_ten_unsolved_recommendations_and_uses_canonical_handle(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = cli_session()

    assert main([" canonical "], client=make_client(session)) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Recommendations for Canonical (rating: 1600)" in captured.out
    assert "Showing 10 recommendations." in captured.out
    assert captured.out.count("   URL:") == 10
    assert captured.out.count("   Reason:") == 10
    assert captured.out.count("Rating: 1600 | Tags: dp, greedy") == 10
    assert "Example Problem" in captured.out
    assert "https://codeforces.com/problemset/problem/" in captured.out
    assert "[1-A]" not in captured.out
    assert [
        (call["url"].rsplit("/", 1)[-1], call["params"]) for call in session.calls
    ] == [
        ("user.info", {"handles": "canonical"}),
        ("user.status", {"handle": "Canonical"}),
        ("problemset.problems", {}),
    ]


def test_cli_reports_nonexistent_handle_without_requesting_more_data(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = FakeSession(
        [
            FakeResponse(
                {
                    "status": "FAILED",
                    "comment": "handles: User with handle missing_user not found",
                },
                status_code=400,
            )
        ]
    )
    assert main(["missing_user"], client=make_client(session)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "missing_user not found" in captured.err
    assert "Traceback" not in captured.err
    assert len(session.calls) == 1


@pytest.mark.parametrize("handle", ["", "   "])
def test_cli_reports_blank_handle_without_network(
    handle: str, capsys: pytest.CaptureFixture[str]
) -> None:
    session = FakeSession([])
    assert main([handle], client=make_client(session)) == 1
    assert "must not be empty" in capsys.readouterr().err
    assert session.calls == []


def test_cli_explains_unrated_user_fallback(capsys: pytest.CaptureFixture[str]) -> None:
    session = cli_session(rating=None, solved=False)
    assert main(["new_user"], client=make_client(session)) == 0
    captured = capsys.readouterr()
    assert "rating: unrated" in captured.out
    assert captured.out.count("Unrated user: using starting rating 800") == 10


@pytest.mark.parametrize("count", [0, 1, 4])
def test_cli_reports_fewer_available_candidates(
    count: int, capsys: pytest.CaptureFixture[str]
) -> None:
    session = cli_session(count=count)
    assert main(["example"], client=make_client(session)) == 0
    captured = capsys.readouterr()
    available = max(count - 1, 0)
    assert captured.out.count("   URL:") == available
    assert captured.err == ""
    if available:
        assert f"Only {available} rated, unsolved problems" in captured.out
    else:
        assert "No rated, unsolved problems are available." in captured.out


def test_cli_reports_network_failure(capsys: pytest.CaptureFixture[str]) -> None:
    class BrokenSession:
        def get(self, *args: Any, **kwargs: Any) -> None:
            raise requests.ConnectionError("Network unavailable")

    assert main(["example"], client=make_client(BrokenSession())) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Could not call Codeforces API" in captured.err
    assert "Traceback" not in captured.err


def test_cli_reports_catalog_error_instead_of_empty_success(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = cli_session()
    session._responses[-1] = FakeResponse(
        {"status": "OK", "result": {"problems": None}}
    )
    assert main(["example"], client=make_client(session)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Expected a problems list" in captured.err
