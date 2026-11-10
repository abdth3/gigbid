"""Typed Pydantic hand-offs exchanged between LangGraph agents (C3)."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class JobSpec(BaseModel):
    job_id: str
    title: str
    deliverables: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    budget_min: float | None = None
    budget_max: float | None = None
    timeline_days: int = 14
    screening_questions: list[str] = Field(default_factory=list)
    hidden_needs: list[str] = Field(default_factory=list)


class RiskReport(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    is_scam: bool = False
    injection_detected: bool = False
    flags: list[str] = Field(default_factory=list)
    explanation: str


class FitReport(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    requirement_matrix: list[dict[str, str]] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class BidDecision(BaseModel):
    action: Literal["bid", "skip", "watch"]
    reason: str


class PriceQuote(BaseModel):
    bid_amount_usd: float = Field(gt=0)
    fair_band_min: float
    fair_band_max: float
    connects_cost: int
    connects_worth_it: bool
    rationale: str


class ProposalDraft(BaseModel):
    job_id: str
    cover_letter: str
    screening_answers: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    strategy: str = "evidence_first"  # used by X2 A/B experiment
    status: str = "pending_review"


class Critique(BaseModel):
    passed: bool
    grounding_ok: bool
    personalisation_ok: bool
    length_ok: bool
    issues: list[str] = Field(default_factory=list)
    revision_number: int = 0


class ComplianceVerdict(BaseModel):
    passed: bool
    blocked_reasons: list[str] = Field(default_factory=list)
    sanitized_cover_letter: str


class ClientIntent(BaseModel):
    intent: Literal["question", "negotiation", "interview_request", "scam_signal", "general"]
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_reply: str
    proposed_slots: list[dict[str, str]] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
