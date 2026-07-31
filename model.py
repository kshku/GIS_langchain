from dotenv import load_dotenv

load_dotenv()

from langchain_openrouter import ChatOpenRouter
from github_api import get_issue_info
from prompts import issue_summary_prompt

llm = ChatOpenRouter(model_name="qwen/qwen3.7-flash", temperature=0.7)


def get_summary(user: str, repo: str, issue_num: int, llm: ChatOpenRouter=llm) -> str:
    issue = get_issue_info(user, repo, issue_num)
    response = llm.invoke(
        issue_summary_prompt.format_messages(
            title=issue["title"],
            body=issue["body"],
            labels=issue["labels"],
        )
    )
    return response.content

if __name__ == "__main__":
    print(get_summary('langchain-ai', 'langchain', 38950))
