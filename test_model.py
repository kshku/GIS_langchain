from unittest import mock

import pytest

import model
from exceptions import GitHubAPIError, LLMError, NotFoundError
from schemas import IssueSummary, PRAnalysis, Severity


class FakeChain:
    def __init__(self, llm):
        self.llm = llm

    def __or__(self, parser):
        return self

    def invoke(self, messages):
        if self.llm.raise_on_invoke:
            raise self.llm.raise_on_invoke
        return self.llm.structured_result


class FakeLLM:
    def __init__(self, structured_result=None):
        self.structured_result = structured_result
        self.raise_on_invoke = None
        self.schema = None
        self.tool_choice = None

    def bind_tools(self, tools, **kwargs):
        self.schema = tools[0]
        self.tool_choice = kwargs.get("tool_choice")
        return FakeChain(self)


def test_get_summary_returns_issue_summary():
    expected = IssueSummary(
        summary="A clear summary",
        key_points=["one", "two"],
        severity=Severity.high,
    )
    llm = FakeLLM(structured_result=expected)
    with mock.patch("model.get_issue_info", return_value={"title": "t", "body": "b", "labels": []}):
        result = model.get_summary("user", "repo", 1, llm=llm)

    assert result is expected
    assert llm.schema is IssueSummary
    assert llm.tool_choice == "auto"


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


def test_analyze_pr_returns_pr_analysis():
    expected = PRAnalysis(
        summary="Refactors the fetcher",
        risks=["Drops error handling"],
        suggested_review="Re-check retry logic before merge",
    )
    llm = FakeLLM(structured_result=expected)
    with mock.patch("model.get_pr_info", return_value={"title": "t", "body": "b", "diff": "d"}):
        result = model.analyze_pr("user", "repo", 1, llm=llm)

    assert result is expected
    assert llm.schema is PRAnalysis
    assert llm.tool_choice == "auto"


def test_analyze_pr_wraps_llm_failure_in_llm_error():
    llm = FakeLLM()
    llm.raise_on_invoke = RuntimeError("rate limited")
    with mock.patch("model.get_pr_info", return_value={"title": "t", "body": "b", "diff": "d"}):
        with pytest.raises(LLMError):
            model.analyze_pr("user", "repo", 1, llm=llm)


def test_analyze_pr_propagates_github_errors():
    llm = FakeLLM()
    with mock.patch("model.get_pr_info", side_effect=NotFoundError("not found")):
        with pytest.raises(NotFoundError):
            model.analyze_pr("user", "repo", 999, llm=llm)

    with mock.patch("model.get_pr_info", side_effect=GitHubAPIError("bad gateway")):
        with pytest.raises(GitHubAPIError):
            model.analyze_pr("user", "repo", 1, llm=llm)
