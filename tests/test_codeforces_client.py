"""Tests for the Codeforces API client."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from src.data.codeforces_client import (
    CodeforcesClient,
    CodeforcesClientError,
    CodeforcesUserNotFoundError,
)


class FakeResponse:
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
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = responses
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        return self._responses.pop(0)


def make_client(session: FakeSession) -> CodeforcesClient:
    return CodeforcesClient(
        session=session,
        min_request_interval_seconds=0,
    )


def test_get_user_profile_returns_handle_and_rating() -> None:
    session = FakeSession(
        [
            FakeResponse(
                {
                    "status": "OK",
                    "result": [{"handle": "tourist", "rating": 3856}],
                }
            )
        ]
    )

    profile = make_client(session).get_user_profile(" tourist ")

    assert profile == {"handle": "tourist", "rating": 3856}
    assert session.calls[0]["params"] == {"handles": "tourist"}


def test_get_user_profile_allows_unrated_user() -> None:
    session = FakeSession(
        [
            FakeResponse(
                {
                    "status": "OK",
                    "result": [{"handle": "new_user"}],
                }
            )
        ]
    )

    profile = make_client(session).get_user_profile("new_user")

    assert profile == {"handle": "new_user", "rating": None}


def test_empty_handle_is_rejected_before_request() -> None:
    session = FakeSession([])

    with pytest.raises(ValueError, match="must not be empty"):
        make_client(session).get_user_profile("   ")

    assert session.calls == []


def test_missing_handle_raises_clear_error() -> None:
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

    with pytest.raises(CodeforcesUserNotFoundError):
        make_client(session).get_user_profile("missing_user")


def test_get_user_submissions_normalizes_response() -> None:
    session = FakeSession(
        [
            FakeResponse(
                {
                    "status": "OK",
                    "result": [
                        {
                            "id": 123,
                            "creationTimeSeconds": 1_700_000_000,
                            "verdict": "OK",
                            "problem": {
                                "contestId": 4,
                                "index": "A",
                                "name": "Watermelon",
                                "rating": 800,
                                "tags": ["brute force", "math"],
                            },
                        }
                    ],
                }
            )
        ]
    )

    submissions = make_client(session).get_user_submissions("tourist")

    assert submissions == [
        {
            "submission_id": 123,
            "creation_time_seconds": 1_700_000_000,
            "verdict": "OK",
            "problem": {
                "contest_id": 4,
                "index": "A",
                "name": "Watermelon",
                "rating": 800,
                "tags": ["brute force", "math"],
            },
        }
    ]
    assert session.calls[0]["params"] == {"handle": "tourist"}


def test_network_error_is_not_returned_as_empty_history() -> None:
    class BrokenSession:
        def get(self, url: str, **kwargs: Any) -> FakeResponse:
            raise requests.ConnectionError("Network unavailable")

    client = CodeforcesClient(
        session=BrokenSession(),
        min_request_interval_seconds=0,
    )

    with pytest.raises(CodeforcesClientError, match="Could not call"):
        client.get_user_submissions("tourist")