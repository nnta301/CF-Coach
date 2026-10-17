"""End-to-end tests for the Codeforces data pipeline."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from src.data.codeforces_client import (
    CodeforcesClient,
    CodeforcesUserNotFoundError,
)
from src.data.user_history import build_user_context


class FakeResponse:
    """Minimal fake HTTP response for deterministic API tests."""

    def __init__(
        self,
        payload: dict[str, Any],
        status_code: int = 200,
    ) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError("HTTP error")

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeSession:
    """Return predefined responses and record outgoing requests."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = responses
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        return self._responses.pop(0)


def make_client(session: FakeSession) -> CodeforcesClient:
    """Create a client without request-rate waiting for tests."""
    return CodeforcesClient(
        session=session,
        min_request_interval_seconds=0,
    )


def make_api_submission(
    *,
    submission_id: int,
    verdict: str | None,
    contest_id: int,
    index: str,
    tags: list[str],
) -> dict[str, Any]:
    """Create one raw Codeforces API submission response."""
    return {
        "id": submission_id,
        "creationTimeSeconds": 1_700_000_000,
        "verdict": verdict,
        "problem": {
            "contestId": contest_id,
            "index": index,
            "name": "Example Problem",
            "rating": 800,
            "tags": tags,
        },
    }


def test_data_pipeline_builds_normalized_user_context_for_valid_handle() -> None:
    session = FakeSession(
        [
            FakeResponse(
                {
                    "status": "OK",
                    "result": [{"handle": "tourist", "rating": 3856}],
                }
            ),
            FakeResponse(
                {
                    "status": "OK",
                    "result": [
                        make_api_submission(
                            submission_id=1,
                            verdict="OK",
                            contest_id=4,
                            index="A",
                            tags=["math", "implementation"],
                        ),
                        make_api_submission(
                            submission_id=2,
                            verdict="WRONG_ANSWER",
                            contest_id=4,
                            index="A",
                            tags=["math", "implementation"],
                        ),
                        make_api_submission(
                            submission_id=3,
                            verdict="OK",
                            contest_id=71,
                            index="A",
                            tags=["implementation"],
                        ),
                    ],
                }
            ),
        ]
    )
    client = make_client(session)

    profile = client.get_user_profile(" tourist ")
    submissions = client.get_user_submissions(profile["handle"])
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
    assert [(call["url"], call["params"]) for call in session.calls] == [
        (
            f"{CodeforcesClient.BASE_URL}/user.info",
            {"handles": "tourist"},
        ),
        (
            f"{CodeforcesClient.BASE_URL}/user.status",
            {"handle": "tourist"},
        ),
    ]


def test_data_pipeline_raises_for_nonexistent_handle() -> None:
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
    client = make_client(session)

    with pytest.raises(CodeforcesUserNotFoundError):
        client.get_user_profile("missing_user")

    assert [(call["url"], call["params"]) for call in session.calls] == [
        (
            f"{CodeforcesClient.BASE_URL}/user.info",
            {"handles": "missing_user"},
        ),
    ]


def test_data_pipeline_returns_empty_history_for_user_with_no_solved_problems() -> None:
    session = FakeSession(
        [
            FakeResponse(
                {
                    "status": "OK",
                    "result": [{"handle": "new_user"}],
                }
            ),
            FakeResponse(
                {
                    "status": "OK",
                    "result": [
                        make_api_submission(
                            submission_id=1,
                            verdict="WRONG_ANSWER",
                            contest_id=4,
                            index="A",
                            tags=["math"],
                        ),
                        make_api_submission(
                            submission_id=2,
                            verdict="TIME_LIMIT_EXCEEDED",
                            contest_id=71,
                            index="A",
                            tags=["implementation"],
                        ),
                    ],
                }
            ),
        ]
    )
    client = make_client(session)

    profile = client.get_user_profile("new_user")
    submissions = client.get_user_submissions(profile["handle"])
    context = build_user_context(profile, submissions)

    assert context == {
        "handle": "new_user",
        "rating": None,
        "solved_problem_ids": [],
        "tag_solve_counts": {},
    }
