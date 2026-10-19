"""Contract and API failure tests for the normalized problem catalog."""

from typing import Any

import pytest
import requests

from src.data.codeforces_client import (
    CodeforcesClient,
    CodeforcesClientError,
    CodeforcesResponseError,
)
from src.data.problem_catalog import fetch_problem_catalog
from tests.test_codeforces_client import FakeResponse, FakeSession, make_client


def raw_problem(**overrides: Any) -> dict[str, Any]:
    return {
        "contestId": 123,
        "index": "A",
        "name": "Example Problem",
        "rating": 1700,
        "tags": ["dp", "greedy"],
        **overrides,
    }


def session_for(problems: list[Any]) -> FakeSession:
    return FakeSession(
        [FakeResponse({"status": "OK", "result": {"problems": problems}})]
    )


def test_catalog_matches_contract_and_requests_problemset() -> None:
    session = session_for([raw_problem()])

    assert fetch_problem_catalog(make_client(session)) == [
        {
            "problem_id": "123-A",
            "name": "Example Problem",
            "rating": 1700,
            "tags": ["dp", "greedy"],
            "url": "https://codeforces.com/problemset/problem/123/A",
        }
    ]
    assert session.calls == [
        {
            "url": f"{CodeforcesClient.BASE_URL}/problemset.problems",
            "params": {},
            "timeout": 10.0,
        }
    ]


def test_catalog_skips_missing_ratings_and_contest_ids() -> None:
    unrated = raw_problem()
    del unrated["rating"]
    no_contest = raw_problem()
    del no_contest["contestId"]
    session = session_for(
        [unrated, raw_problem(rating=None), no_contest, raw_problem(contestId=None)]
    )

    assert fetch_problem_catalog(make_client(session)) == []


def test_catalog_keeps_first_duplicate_and_unique_tags() -> None:
    session = session_for(
        [raw_problem(tags=["dp", "dp"]), raw_problem(name="Duplicate")]
    )

    catalog = fetch_problem_catalog(make_client(session))

    assert len(catalog) == 1
    assert catalog[0]["name"] == "Example Problem"
    assert catalog[0]["tags"] == ["dp"]


def test_catalog_allows_empty_catalog_and_missing_tags() -> None:
    assert fetch_problem_catalog(make_client(session_for([]))) == []
    problem = raw_problem()
    del problem["tags"]
    assert fetch_problem_catalog(make_client(session_for([problem])))[0]["tags"] == []


@pytest.mark.parametrize("result", [None, [], {}, {"problems": None}])
def test_catalog_rejects_invalid_api_result(result: Any) -> None:
    client = make_client(
        FakeSession([FakeResponse({"status": "OK", "result": result})])
    )

    with pytest.raises(CodeforcesResponseError, match="problems list"):
        fetch_problem_catalog(client)


@pytest.mark.parametrize(
    "problem",
    [
        None,
        raw_problem(contestId="123"),
        raw_problem(contestId=True),
        raw_problem(contestId=0),
        raw_problem(rating="1700"),
        raw_problem(rating=True),
        raw_problem(rating=-1),
        raw_problem(index=""),
        raw_problem(name=None),
        raw_problem(tags="dp"),
        raw_problem(tags=[1]),
    ],
)
def test_catalog_rejects_malformed_problem(problem: Any) -> None:
    with pytest.raises(CodeforcesResponseError):
        fetch_problem_catalog(make_client(session_for([problem])))


def test_catalog_propagates_api_failure() -> None:
    session = FakeSession(
        [FakeResponse({"status": "FAILED", "comment": "Call limit exceeded"})]
    )
    with pytest.raises(CodeforcesClientError, match="Call limit exceeded"):
        fetch_problem_catalog(make_client(session))


def test_catalog_propagates_network_failure() -> None:
    class BrokenSession:
        def get(self, *args: Any, **kwargs: Any) -> None:
            raise requests.ConnectionError("Network unavailable")

    with pytest.raises(CodeforcesClientError, match="Could not call"):
        fetch_problem_catalog(CodeforcesClient(session=BrokenSession()))
