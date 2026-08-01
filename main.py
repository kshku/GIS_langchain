import argparse
import sys
import time

import httpx
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from openrouter.errors import OpenRouterError

from exceptions import GitHubAPIError, LLMError, NotFoundError
from github_api import get_issue_info, get_pr_info
from model import llm
from prompts import issue_summary_prompt, pr_analysis_prompt
from schemas import IssueSummary, PRAnalysis

_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3

_sleep = time.sleep


def build_issue_chain(llm=llm):
    return (
        issue_summary_prompt
        | llm.bind_tools([IssueSummary], tool_choice="auto")
        | PydanticToolsParser(tools=[IssueSummary], first_tool_only=True)
    )


def build_pr_chain(llm=llm):
    return (
        pr_analysis_prompt
        | llm.bind_tools([PRAnalysis], tool_choice="auto")
        | PydanticToolsParser(tools=[PRAnalysis], first_tool_only=True)
    )


def print_issue_summary(result):
    print(f"Summary: {result.summary}")
    print("Key points:")
    for point in result.key_points:
        print(f"  - {point}")
    print(f"Severity: {result.severity.value}")


def print_pr_analysis(result):
    print(f"Summary: {result.summary}")
    print("Risks:")
    for risk in result.risks:
        print(f"  - {risk}")
    print(f"Suggested review: {result.suggested_review}")


def _is_retryable(e) -> bool:
    if isinstance(e, OpenRouterError):
        return e.status_code in _RETRY_STATUSES
    return isinstance(e, httpx.TransportError)


def _run_chain(chain, inputs):
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            if attempt == _MAX_ATTEMPTS - 1 or not _is_retryable(e):
                raise LLMError(f"LLM call failed: {e}") from e
            _sleep(2 ** attempt)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="GitHub issue summarizer and PR analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    issue_parser = subparsers.add_parser("issue", help="Summarize a GitHub issue")
    issue_parser.add_argument("user")
    issue_parser.add_argument("repo")
    issue_parser.add_argument("number", type=int)

    pr_parser = subparsers.add_parser("pr", help="Analyze a GitHub pull request")
    pr_parser.add_argument("user")
    pr_parser.add_argument("repo")
    pr_parser.add_argument("number", type=int)

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "issue":
            issue = get_issue_info(args.user, args.repo, args.number)
            result = _run_chain(build_issue_chain(), issue)
            print_issue_summary(result)
        else:
            pr = get_pr_info(args.user, args.repo, args.number)
            result = _run_chain(build_pr_chain(), pr)
            print_pr_analysis(result)
    except (NotFoundError, GitHubAPIError, LLMError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
