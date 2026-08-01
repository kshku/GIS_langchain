from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class IssueSummary(BaseModel):
    summary: str
    key_points: list[str]
    severity: Severity


class PRAnalysis(BaseModel):
    summary: str
    risks: list[str]
    suggested_review: str
