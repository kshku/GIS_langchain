from unittest import mock

import pytest

import model
from exceptions import GitHubAPIError, LLMError, NotFoundError


class FakeLLM:
    def __init__(self, content="summary"):
        self.content = content
        self.raise_on_invoke = None

    def invoke(self, messages):
        if self.raise_on_invoke:
            raise self.raise_on_invoke
        return mock.Mock(content=self.content)


def test_get_summary_returns_llm_content():
    llm = FakeLLM(content="A clear summary")
    with mock.patch("model.get_issue_info", return_value={"title": "t", "body": "b", "labels": []}):
        result = model.get_summary("user", "repo", 1, llm=llm)

    assert result == "A clear summary"


def test_get_summary_wraps_llm_failure_in_llm_error():
    llm = FakeLLM()
    llm.raise_on_invoke = RuntimeError("rate limited")
    with mock.patch("model.get_issue_info", return_value={"title": "t", "body": "b", "labels": []}):
        with pytest.raises(LLMError):
            model.get_summary("user", "repo", 1, llm=llm)


def test_get_summary_propagates_github_errors():
    llm = FakeLLM()
    with mock.patch("model.get_issue_info", side_effect=NotFoundError("not found")):
        with pytest.raises(NotFoundError):
            model.get_summary("user", "repo", 999, llm=llm)

    with mock.patch("model.get_issue_info", side_effect=GitHubAPIError("bad gateway")):
        with pytest.raises(GitHubAPIError):
            model.get_summary("user", "repo", 1, llm=llm)
