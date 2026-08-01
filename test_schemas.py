import pytest
from pydantic import ValidationError

from schemas import IssueSummary, PRAnalysis, Severity


def test_issue_summary_accepts_valid_fields():
    summary = IssueSummary(
        summary="Something broke",
        key_points=["point one", "point two"],
        severity=Severity.high,
    )

    assert summary.summary == "Something broke"
    assert summary.key_points == ["point one", "point two"]
    assert summary.severity == Severity.high


def test_issue_summary_accepts_string_severity():
    summary = IssueSummary(
        summary="Something broke",
        key_points=[],
        severity="medium",
    )

    assert summary.severity == Severity.medium


def test_issue_summary_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        IssueSummary(summary="s", key_points=[], severity="critical")


def test_issue_summary_requires_fields():
    with pytest.raises(ValidationError):
        IssueSummary(summary="s")


def test_pr_analysis_accepts_valid_fields():
    analysis = PRAnalysis(
        summary="Refactors the fetcher",
        risks=["Drops error handling"],
        suggested_review="Re-check retry logic before merge",
    )

    assert analysis.summary == "Refactors the fetcher"
    assert analysis.risks == ["Drops error handling"]
    assert analysis.suggested_review == "Re-check retry logic before merge"


def test_pr_analysis_requires_fields():
    with pytest.raises(ValidationError):
        PRAnalysis(summary="s")
