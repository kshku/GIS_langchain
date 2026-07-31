from unittest import mock

import pytest
import requests

import github_api
from exceptions import GitHubAPIError, NotFoundError


class FakeResponse:
    def __init__(self, status_code, payload=None, text=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._payload


ISSUE_PAYLOAD = {"title": "Bug", "body": "It crashes", "labels": ["bug"]}


@mock.patch("github_api._sleep")
@mock.patch("requests.get")
def test_get_issue_info_returns_parsed_issue(mock_get, mock_sleep):
    mock_get.return_value = FakeResponse(200, ISSUE_PAYLOAD)

    issue = github_api.get_issue_info("user", "repo", 1)

    assert issue == {"title": "Bug", "body": "It crashes", "labels": ["bug"]}


@mock.patch("github_api._sleep")
@mock.patch("requests.get")
def test_get_issue_info_retries_on_5xx_then_succeeds(mock_get, mock_sleep):
    mock_get.side_effect = [
        FakeResponse(503, {"message": "unavailable"}),
        FakeResponse(503, {"message": "unavailable"}),
        FakeResponse(200, ISSUE_PAYLOAD),
    ]

    issue = github_api.get_issue_info("user", "repo", 1)

    assert issue["title"] == "Bug"
    assert mock_get.call_count == 3


@mock.patch("github_api._sleep")
@mock.patch("requests.get")
def test_get_issue_info_raises_after_exhausting_retries(mock_get, mock_sleep):
    mock_get.side_effect = [FakeResponse(500, {"message": "oops"})] * 3

    with pytest.raises(GitHubAPIError):
        github_api.get_issue_info("user", "repo", 1)

    assert mock_get.call_count == 3


@mock.patch("github_api._sleep")
@mock.patch("requests.get")
def test_get_issue_info_raises_not_found(mock_get, mock_sleep):
    mock_get.return_value = FakeResponse(404, {"message": "Not Found"})

    with pytest.raises(NotFoundError):
        github_api.get_issue_info("user", "repo", 999)


@mock.patch("github_api._sleep")
@mock.patch("requests.get")
def test_get_issue_info_retries_on_network_error(mock_get, mock_sleep):
    mock_get.side_effect = [requests.ConnectionError("boom"), FakeResponse(200, ISSUE_PAYLOAD)]

    issue = github_api.get_issue_info("user", "repo", 1)

    assert issue["title"] == "Bug"
    assert mock_get.call_count == 2


@mock.patch("github_api._sleep")
@mock.patch("requests.get")
def test_get_pr_info_includes_diff(mock_get, mock_sleep):
    mock_get.side_effect = [
        FakeResponse(200, {"title": "Fix", "body": "Fixes bug", "diff_url": "https://github.com/u/r/pull/1.diff"}),
        FakeResponse(200, text="diff --git a/foo b/foo\n+line"),
    ]

    pr = github_api.get_pr_info("user", "repo", 1)

    assert pr == {"title": "Fix", "body": "Fixes bug", "diff": "diff --git a/foo b/foo\n+line"}


@mock.patch("github_api._sleep")
@mock.patch("requests.get")
def test_get_pr_info_raises_not_found(mock_get, mock_sleep):
    mock_get.return_value = FakeResponse(404, {"message": "Not Found"})

    with pytest.raises(NotFoundError):
        github_api.get_pr_info("user", "repo", 999)
