class GISError(Exception):
    """Base exception for the app."""


class GitHubAPIError(GISError):
    """Raised when a GitHub API request fails."""


class NotFoundError(GitHubAPIError):
    """Raised when the requested resource does not exist."""


class LLMError(GISError):
    """Raised when an LLM call fails."""
