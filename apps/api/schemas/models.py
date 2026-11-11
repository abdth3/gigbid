"""Pydantic schemas for FastAPI OpenAPI contract & TypeScript client generation."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class OnboardingRequest(BaseModel):
    persona: str = "ai_ml_engineer"
    hourly_rate_usd: float = 55.0
    weekly_connects_budget: int = 60
    marketplace_mode: Literal["gigsim", "upwork_live"] = "gigsim"
    oauth_token: str | None = None


class PortfolioUploadRequest(BaseModel):
    title: str
    summary: str
    skills: list[str] = Field(default_factory=list)
    industry: str = "SaaS"
    outcome: str = "delivered"


class AnalyzeJobRequest(BaseModel):
    job_id: str
    strategy: str = "evidence_first"


class ApprovalActionRequest(BaseModel):
    action: Literal["approve", "edit", "reject"]
    edited_cover_letter: str | None = None
    reason: str = ""


class RegenerateParagraphRequest(BaseModel):
    paragraph_index: int = 0
    instruction: str = "Make more concise and cite evidence"


class MessageReplyRequest(BaseModel):
    job_id: str
    action: Literal["approve", "edit", "reject"] = "approve"
    edited_reply: str | None = None


class SettingsUpdateRequest(BaseModel):
    autonomy_level: Literal["manual_approve", "auto_skip_low_fit"] = "manual_approve"
    weekly_connects_budget: int = 60
    marketplace_mode: Literal["gigsim", "upwork_live"] = "gigsim"
    rag_variant: str = "v4_outcome"
    saved_searches: list[str] = Field(default_factory=list)


class JobSummary(BaseModel):
    job_id: str
    title: str
    description: str
    required_skills: list[str]
    budget: dict[str, Any]
    connects_cost: int
    fit_score: float = 0.0
    risk_score: float = 0.0
    is_scam: bool = False
    recommended_action: str = "pending"
    status: str = "inbox"
    thread_id: str | None = None
