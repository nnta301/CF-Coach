"""Client for the public Codeforces API."""

from __future__ import annotations

import time
from typing import Any

import requests


class CodeforcesClientError(RuntimeError):
    """Base error for Codeforces API client failures."""


class CodeforcesUserNotFoundError(CodeforcesClientError):
    """Raised when a requested Codeforces handle does not exist."""


class CodeforcesResponseError(CodeforcesClientError):
    """Raised when Codeforces returns an unexpected response."""


class CodeforcesClient:
    """Fetch and normalize public Codeforces user data."""

    BASE_URL = "https://codeforces.com/api"

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout_seconds: float = 10.0,
        min_request_interval_seconds: float = 2.1,
    ) -> None:
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds
        self._min_request_interval_seconds = min_request_interval_seconds
        self._last_request_time: float | None = None

    def get_user_profile(self, handle: str) -> dict[str, str | int | None]:
        """Return the canonical handle and current rating for a user."""
        normalized_handle = self._validate_handle(handle)

        result = self._request(
            method="user.info",
            params={"handles": normalized_handle},
        )

        if not isinstance(result, list) or len(result) != 1:
            raise CodeforcesResponseError(
                "Expected exactly one user in the user.info response."
            )

        user = result[0]
        if not isinstance(user, dict):
            raise CodeforcesResponseError("Invalid user.info response format.")

        response_handle = user.get("handle")
        if not isinstance(response_handle, str):
            raise CodeforcesResponseError("User response does not contain a handle.")

        rating = user.get("rating")
        if rating is not None and not isinstance(rating, int):
            raise CodeforcesResponseError("User rating has an invalid format.")

        return {
            "handle": response_handle,
            "rating": rating,
        }

    def get_user_submissions(self, handle: str) -> list[dict[str, Any]]:
        """Return normalized public submission history for a user."""
        normalized_handle = self._validate_handle(handle)

        result = self._request(
            method="user.status",
            params={"handle": normalized_handle},
        )

        if not isinstance(result, list):
            raise CodeforcesResponseError(
                "Expected a list in the user.status response."
            )

        return [self._normalize_submission(submission) for submission in result]

    def _request(self, method: str, params: dict[str, str]) -> Any:
        """Call one Codeforces API endpoint and return its result field."""
        self._wait_before_request()

        try:
            response = self._session.get(
                f"{self.BASE_URL}/{method}",
                params=params,
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as error:
            raise CodeforcesClientError(
                f"Could not call Codeforces API method '{method}'."
            ) from error

        self._last_request_time = time.monotonic()

        try:
            payload = response.json()
        except ValueError as error:
            raise CodeforcesResponseError(
                f"Codeforces API method '{method}' returned invalid JSON."
            ) from error

        if isinstance(payload, dict) and payload.get("status") == "FAILED":
            comment = str(payload.get("comment", "Unknown Codeforces API error."))
            if "not found" in comment.lower():
                raise CodeforcesUserNotFoundError(comment)
            raise CodeforcesClientError(comment)

        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise CodeforcesClientError(
                f"Codeforces API method '{method}' returned HTTP "
                f"{response.status_code}."
            ) from error

        if not isinstance(payload, dict):
            raise CodeforcesResponseError(
                f"Codeforces API method '{method}' returned an invalid payload."
            )

        if payload.get("status") != "OK":
            raise CodeforcesResponseError(
                f"Codeforces API method '{method}' returned an unexpected status."
            )

        if "result" not in payload:
            raise CodeforcesResponseError(
                f"Codeforces API method '{method}' did not return a result."
            )

        return payload["result"]

    def _wait_before_request(self) -> None:
        """Respect Codeforces public API request limits."""
        if self._last_request_time is None:
            return

        elapsed = time.monotonic() - self._last_request_time
        remaining = self._min_request_interval_seconds - elapsed

        if remaining > 0:
            time.sleep(remaining)

    @staticmethod
    def _validate_handle(handle: str) -> str:
        """Validate and normalize a Codeforces handle."""
        if not isinstance(handle, str):
            raise TypeError("Codeforces handle must be a string.")

        normalized_handle = handle.strip()
        if not normalized_handle:
            raise ValueError("Codeforces handle must not be empty.")

        return normalized_handle

    @staticmethod
    def _normalize_submission(submission: Any) -> dict[str, Any]:
        """Normalize one Codeforces submission for downstream processing."""
        if not isinstance(submission, dict):
            raise CodeforcesResponseError("Invalid submission format.")

        problem = submission.get("problem")
        if not isinstance(problem, dict):
            raise CodeforcesResponseError("Submission does not contain a problem.")

        submission_id = submission.get("id")
        creation_time_seconds = submission.get("creationTimeSeconds")
        problem_index = problem.get("index")
        problem_name = problem.get("name")
        problem_tags = problem.get("tags", [])

        if not isinstance(submission_id, int):
            raise CodeforcesResponseError("Submission does not contain a valid id.")

        if not isinstance(creation_time_seconds, int):
            raise CodeforcesResponseError(
                "Submission does not contain a valid creation time."
            )

        if not isinstance(problem_index, str) or not isinstance(problem_name, str):
            raise CodeforcesResponseError("Problem data has an invalid format.")

        if not isinstance(problem_tags, list) or not all(
            isinstance(tag, str) for tag in problem_tags
        ):
            raise CodeforcesResponseError("Problem tags have an invalid format.")

        contest_id = problem.get("contestId")
        if contest_id is not None and not isinstance(contest_id, int):
            raise CodeforcesResponseError("Problem contest id has an invalid format.")

        rating = problem.get("rating")
        if rating is not None and not isinstance(rating, int):
            raise CodeforcesResponseError("Problem rating has an invalid format.")

        verdict = submission.get("verdict")
        if verdict is not None and not isinstance(verdict, str):
            raise CodeforcesResponseError("Submission verdict has an invalid format.")

        return {
            "submission_id": submission_id,
            "creation_time_seconds": creation_time_seconds,
            "verdict": verdict,
            "problem": {
                "contest_id": contest_id,
                "index": problem_index,
                "name": problem_name,
                "rating": rating,
                "tags": problem_tags,
            },
        }