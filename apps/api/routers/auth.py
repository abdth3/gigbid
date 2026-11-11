"""Authentication, onboarding, portfolio upload & evidence deletion routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from apps.api.auth.security import (
    USERS,
    authenticate_user,
    get_current_user,
    store_oauth_token,
)
from apps.api.schemas.models import LoginRequest, OnboardingRequest, PortfolioUploadRequest
from rag.ingest.loader import get_corpus_store

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(req: LoginRequest):
    res = authenticate_user(req.username, req.password)
    if not res:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return res


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {k: v for k, v in user.items() if k != "password_hash"}


@router.post("/onboarding")
def onboarding(req: OnboardingRequest, user: dict = Depends(get_current_user)):
    u = USERS[user["user_id"]]
    u["persona"] = req.persona
    u["hourly_rate_usd"] = req.hourly_rate_usd
    u["weekly_connects_budget"] = req.weekly_connects_budget
    if req.oauth_token:
        store_oauth_token(user["user_id"], req.oauth_token)
    return {"status": "onboarded", "user": {k: v for k, v in u.items() if k != "password_hash"}}


@router.get("/portfolio")
def list_portfolio(user: dict = Depends(get_current_user)):
    persona = user.get("persona", "ai_ml_engineer")
    chunks = get_corpus_store().get_chunks(persona)
    seen = {}
    for c in chunks:
        if c.evidence_id not in seen:
            seen[c.evidence_id] = {
                "evidence_id": c.evidence_id,
                "type": c.type,
                "title": c.title,
                "summary": c.text,
                "skills": c.skills,
                "industry": c.client_industry,
                "outcome": c.outcome,
            }
    return {"persona": persona, "items": list(seen.values())}


@router.post("/portfolio")
def upload_portfolio(req: PortfolioUploadRequest, user: dict = Depends(get_current_user)):
    persona = user.get("persona", "ai_ml_engineer")
    chunk = get_corpus_store().add_evidence(persona, req.model_dump())
    return {"status": "indexed", "evidence_id": chunk.evidence_id}


@router.delete("/portfolio/{evidence_id}")
def delete_portfolio_evidence(evidence_id: str, user: dict = Depends(get_current_user)):
    persona = user.get("persona", "ai_ml_engineer")
    removed = get_corpus_store().delete_evidence(persona, evidence_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Evidence item not found")
    return {"status": "deleted", "evidence_id": evidence_id}
