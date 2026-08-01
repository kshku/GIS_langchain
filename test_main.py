import httpx
import pytest

from exceptions import LLMError, NotFoundError
from openrouter.errors import OpenRouterError
from schemas import IssueSummary, PRAnalysis, Severity
import main


class FakeChain:
    def __init__(self, result=None, error=None, errors=None):
        self.result = result
        self.error = error
        self.errors = list(errors) if errors else []
        self.invoked_inputs = None
        self.inputs_log = []
        self.invoke_count = 0

    def invoke(self, inputs):
        self.invoked_inputs = inputs
        self.inputs_log.append(inputs)
        self.invoke_count += 1
        if self.errors:
            raise self.errors.pop(0)
        if self.error:
            raise self.error
        return self.result


def make_provider_error(status_code):
    return OpenRouterError("boom", httpx.Response(status_code, request=httpx.Request("POST", "https://x")))


def test_parse_args_issue():
    args = main.parse_args(["issue", "langchain-ai", "langchain", "38950"])
    assert args.command == "issue"
    assert args.user == "langchain-ai"
    assert args.repo == "langchain"
    assert args.number == 38950


def test_parse_args_pr():
    args = main.parse_args(["pr", "langchain-ai", "langchain", "1000"])
    assert args.command == "pr"
    assert args.user == "langchain-ai"
    assert args.repo == "langchain"
    assert args.number == 1000


def test_issue_chain_is_pipe():
    props = main.build_issue_chain().input_schema.model_json_schema()["properties"]
    assert set(props) == {"title", "body", "labels"}


def test_pr_chain_is_pipe():
    props = main.build_pr_chain().input_schema.model_json_schema()["properties"]
    assert set(props) == {"title", "body", "diff"}


def test_print_issue_summary(capsys):
    result = IssueSummary(
        summary="Fix the bug", key_points=["point one", "point two"], severity=Severity.high
    )
    main.print_issue_summary(result)
    out = capsys.readouterr().out
    assert "Fix the bug" in out
    assert "- point one" in out
    assert "- point two" in out
    assert "Severity: high" in out


def test_print_pr_analysis(capsys):
    result = PRAnalysis(
        summary="Adds a feature", risks=["risk one"], suggested_review="look at x"
    )
    main.print_pr_analysis(result)
    out = capsys.readouterr().out
    assert "Adds a feature" in out
    assert "- risk one" in out
    assert "look at x" in out


def test_main_issue_flow(monkeypatch, capsys):
    issue = {"title": "t", "body": "b", "labels": ["x"]}
    result = IssueSummary(
        summary="S", key_points=["a", "b"], severity=Severity.medium
    )
    chain = FakeChain(result=result)
    monkeypatch.setattr(main, "get_issue_info", lambda u, r, n: issue)
    monkeypatch.setattr(main, "build_issue_chain", lambda: chain)

    exit_code = main.main(["issue", "u", "r", "1"])

    assert exit_code == 0
    assert chain.invoked_inputs == issue
    out = capsys.readouterr().out
    assert "S" in out
    assert "- a" in out
    assert "Severity: medium" in out


def test_main_pr_flow(monkeypatch, capsys):
    pr = {"title": "t", "body": "b", "diff": "d"}
    result = PRAnalysis(summary="S", risks=["r"], suggested_review="sr")
    chain = FakeChain(result=result)
    monkeypatch.setattr(main, "get_pr_info", lambda u, r, n: pr)
    monkeypatch.setattr(main, "build_pr_chain", lambda: chain)

    exit_code = main.main(["pr", "u", "r", "1"])

    assert exit_code == 0
    assert chain.invoked_inputs == pr
    out = capsys.readouterr().out
    assert "S" in out
    assert "- r" in out


def test_main_issue_llm_error(monkeypatch, capsys):
    chain = FakeChain(error=RuntimeError("boom"))
    monkeypatch.setattr(main, "get_issue_info", lambda u, r, n: {})
    monkeypatch.setattr(main, "build_issue_chain", lambda: chain)

    exit_code = main.main(["issue", "u", "r", "1"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "LLM call failed: boom" in err


def test_main_issue_github_error(monkeypatch, capsys):
    def raise_not_found(u, r, n):
        raise NotFoundError("not found")

    monkeypatch.setattr(main, "get_issue_info", raise_not_found)

    exit_code = main.main(["issue", "u", "r", "999"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_run_chain_wraps_error(monkeypatch):
    chain = FakeChain(error=ValueError("bad"))
    with pytest.raises(LLMError, match="LLM call failed: bad"):
        main._run_chain(chain, {})
    assert chain.invoke_count == 1


def test_run_chain_retries_transient_error_then_succeeds(monkeypatch):
    chain = FakeChain(
        result="ok", errors=[make_provider_error(503), make_provider_error(429)]
    )
    monkeypatch.setattr(main, "_sleep", lambda s: None)

    result = main._run_chain(chain, {})

    assert result == "ok"
    assert chain.invoke_count == 3
    assert len(chain.inputs_log) == 3


def test_run_chain_gives_up_after_max_attempts(monkeypatch):
    chain = FakeChain(errors=[make_provider_error(503)] * 3)
    monkeypatch.setattr(main, "_sleep", lambda s: None)

    with pytest.raises(LLMError, match="LLM call failed"):
        main._run_chain(chain, {})

    assert chain.invoke_count == 3
