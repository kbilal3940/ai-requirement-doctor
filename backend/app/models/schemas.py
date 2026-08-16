"""
Pydantic v2 models. Two jobs:
  1. Validate what comes in/out of our own API (Analyze*, Enhance*).
  2. Validate the *shape* of whatever JSON the AI model hands back, so a
     malformed/hallucinated response never reaches the client untyped.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

Severity = Literal["critical", "important", "minor"]
Category = Literal["ambiguity", "missing", "conflict", "other"]


# ---------- shared ----------

class Issue(BaseModel):
    severity: Severity
    category: Category
    title: str
    explanation: str


# ---------- /api/analyze ----------

class AnalyzeRequest(BaseModel):
    requirement_text: str = Field(..., description="Raw requirement statement text")

    @field_validator("requirement_text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("requirement_text must not be empty")
        return v


class AnalyzeResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    issues: list[Issue]
    suggested_rewrite: str


# What we ask the AI to return for analysis. Same shape as AnalyzeResponse,
# kept separate so a change in our public API doesn't silently change what
# we require from the model prompt.
class AIAnalysisPayload(BaseModel):
    score: int = Field(..., ge=0, le=100)
    issues: list[Issue]
    suggested_rewrite: str


# ---------- /api/enhance ----------

class EnhanceRequest(BaseModel):
    requirement_text: str = Field(..., description="The original requirement text")
    issues: list[Issue] = Field(
        default_factory=list,
        description="Issues from the prior /api/analyze call that the user confirmed they want addressed",
    )
    user_notes: Optional[str] = Field(
        default=None,
        description="Optional extra context/answers the user supplied when confirming (e.g. actual concurrency target)",
    )

    @field_validator("requirement_text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("requirement_text must not be empty")
        return v


class EnhanceResponse(BaseModel):
    enhanced_requirement: str
    new_score: int = Field(..., ge=0, le=100)
    summary_of_changes: list[str]


class AIEnhancementPayload(BaseModel):
    enhanced_requirement: str
    new_score: int = Field(..., ge=0, le=100)
    summary_of_changes: list[str]


# ---------- errors ----------

class ErrorResponse(BaseModel):
    detail: str
