from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

issue_summary_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "You are an expert software engineer. Summarize the following GitHub issue "
            "clearly and concisely. Cover what the problem is, why it matters, and any "
            "context or hints from the labels."
        ),
        HumanMessagePromptTemplate.from_template(
            "Title: {title}\n"
            "Labels: {labels}\n"
            "Body:\n{body}"
        ),
    ]
)

pr_analysis_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "You are an expert code reviewer. Analyze the following pull request. "
            "Summarize what it changes, assess potential risks or bugs, and note "
            "anything that needs attention before merge."
        ),
        HumanMessagePromptTemplate.from_template(
            "Title: {title}\n"
            "Body:\n{body}\n"
            "Diff:\n{diff}"
        ),
    ]
)
