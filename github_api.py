import requests

def _get_issue(user: str, repo: str, issue_num: int) -> dict:
    res = requests.get(f"https://api.github.com/repos/{user}/{repo}/issues/{issue_num}").json()
    if "message" in res:
        return None
    return res

def get_issue_info(user: str, repo: str, issue_num: int) -> dict:
    res = _get_issue(user, repo,issue_num)
    if res == None:
        return {"": ""}
    return {
        "title": res["title"],
        "body": res["body"],
        "labels": res["labels"],
    }

def _get_pr(user: str, repo: str, pr_num: int) -> dict:
    res = requests.get(f"https://api.github.com/repos/{user}/{repo}/pulls/{pr_num}").json()
    if "message" in res:
        return None
    return res

def get_pr_info(user: str, repo: str, pr_num: int) -> dict:
    res = _get_pr(user, repo, pr_num)
    if res == None:
        return {"": ""}
    return {
        "title": res["title"],
        "body": res["body"],
        "diff": requests.get(res["diff_url"]).text,
    }

if __name__ == "__main__":
    print(_get_issue('kshku', 'GIS_langchain', 1))
    print(get_issue_info("kshku", "GIS_langchain", 1))
    print(_get_pr('langchain-ai', 'langchain', 1))
    print(get_pr_info('langchain-ai', 'langchain', 1))
