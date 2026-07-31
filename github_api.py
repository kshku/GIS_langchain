import time

import requests

from exceptions import GitHubAPIError, NotFoundError

_API_BASE = "https://api.github.com"
_RETRY_STATUSES = {403, 429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3

_sleep = time.sleep


def _get_with_retries(url: str) -> requests.Response:
    for attempt in range(_MAX_ATTEMPTS):
        try:
            res = requests.get(url)
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == _MAX_ATTEMPTS - 1:
                raise GitHubAPIError(f"Request failed for {url}: {e}") from e
            _sleep(2 ** attempt)
            continue
        if res.status_code == 404:
            raise NotFoundError(f"Resource not found: {url}")
        if res.status_code in _RETRY_STATUSES and attempt < _MAX_ATTEMPTS - 1:
            _sleep(int(res.headers.get("Retry-After") or 2 ** attempt))
            continue
        if res.status_code != 200:
            raise GitHubAPIError(f"GitHub API error {res.status_code} for {url}")
        return res
    raise GitHubAPIError(f"Request failed for {url}")


def _get_issue(user: str, repo: str, issue_num: int) -> dict:
    return _get_with_retries(f"{_API_BASE}/repos/{user}/{repo}/issues/{issue_num}").json()


def get_issue_info(user: str, repo: str, issue_num: int) -> dict:
    res = _get_issue(user, repo, issue_num)
    return {
        "title": res["title"],
        "body": res["body"],
        "labels": res["labels"],
    }


def _get_pr(user: str, repo: str, pr_num: int) -> dict:
    return _get_with_retries(f"{_API_BASE}/repos/{user}/{repo}/pulls/{pr_num}").json()


def get_pr_info(user: str, repo: str, pr_num: int) -> dict:
    res = _get_pr(user, repo, pr_num)
    return {
        "title": res["title"],
        "body": res["body"],
        "diff": _get_with_retries(res["diff_url"]).text,
    }


if __name__ == "__main__":
    print(get_issue_info("kshku", "GIS_langchain", 1))
    print(get_pr_info("langchain-ai", "langchain", 1))
