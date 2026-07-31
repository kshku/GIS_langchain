import requests

def _get_issue(user: str, repo: str, issue_num: int) -> dict:
    try:
        return requests.get(f"https://api.github.com/repos/{user}/{repo}/issues/{issue_num}").json()
    except requests.exceptions.HTTPError as e:
        return None

def get_issue_info(user: str, repo: str, issue_num: int) -> dict:
    res = _get_issue(user, repo,issue_num)
    if res == None:
        return {"": ""}
    return {
        "title": res["title"],
        "body": res["body"],
        "labels": res["labels"],
    }

if __name__ == "__main__":
    print(_get_issue('kshku', 'GIS_langchain', 1))
    print(get_issue_info("kshku", "GIS_langchain", 1))
