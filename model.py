from dotenv import load_dotenv

load_dotenv()

from langchain_openrouter import ChatOpenRouter
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from exceptions import LLMError
from github_api import get_issue_info, get_pr_info
from prompts import issue_summary_prompt, pr_analysis_prompt
from schemas import IssueSummary, PRAnalysis

llm = ChatOpenRouter(model_name="qwen/qwen3.7-flash", temperature=0.7)


def _structured_chain(llm, schema):
    return (
        llm.bind_tools([schema], tool_choice="auto")
        | PydanticToolsParser(tools=[schema], first_tool_only=True)
    )


def get_summary(user: str, repo: str, issue_num: int, llm: ChatOpenRouter=llm) -> IssueSummary:
    issue = get_issue_info(user, repo, issue_num)
    try:
        return _structured_chain(llm, IssueSummary).invoke(
            issue_summary_prompt.format_messages(
                title=issue["title"],
                body=issue["body"],
                labels=issue["labels"],
            )
        )
    except Exception as e:
        raise LLMError(f"LLM call failed: {e}") from e


def analyze_pr(user: str, repo: str, pr_num: int, llm: ChatOpenRouter=llm) -> PRAnalysis:
    pr = get_pr_info(user, repo, pr_num)
    try:
        return _structured_chain(llm, PRAnalysis).invoke(
            pr_analysis_prompt.format_messages(
                title=pr["title"],
                body=pr["body"],
                diff=pr["diff"],
            )
        )
    except Exception as e:
        raise LLMError(f"LLM call failed: {e}") from e

if __name__ == "__main__":
    print(get_summary('langchain-ai', 'langchain', 38950))
    print(analyze_pr('langchain-ai', 'langchain', 1000))
