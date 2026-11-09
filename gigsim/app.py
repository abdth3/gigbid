"""GigSim Marketplace Simulator FastAPI service."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from gigsim.store import RateLimitExceeded, SimulatedServerError, get_gigsim_store

app = FastAPI(title="GigSim Marketplace Simulator", version="1.0.0")


class DraftRequest(BaseModel):
    user_id: str = "default-user"
    job_id: str
    cover_letter: str
    bid_amount_usd: float = Field(gt=0)
    screening_answers: list[str] = Field(default_factory=list)
    idempotency_key: str
    dry_run: bool = False


class SubmitRequest(BaseModel):
    user_id: str = "default-user"
    draft_id: str
    idempotency_key: str
    dry_run: bool = False


class MessageRequest(BaseModel):
    user_id: str = "default-user"
    job_id: str
    text: str
    idempotency_key: str
    dry_run: bool = False


def verify_token(authorization: str | None = Header(default=None)) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    return "local-dev-token"


@app.get("/health")
def health():
    return {"status": "ok", "service": "gigsim"}


@app.get("/jobs")
def search_jobs(
    query: str = "",
    limit: int = Query(default=20, ge=1, le=100),
    persona: str | None = None,
    user_id: str = "default-user",
    _token: str = Depends(verify_token),
):
    store = get_gigsim_store()
    try:
        store.check_rate_limit(user_id)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except SimulatedServerError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"jobs": store.search_jobs(query=query, limit=limit, persona=persona)}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, user_id: str = "default-user", _token: str = Depends(verify_token)):
    store = get_gigsim_store()
    try:
        store.check_rate_limit(user_id)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except SimulatedServerError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/clients/{client_id}")
def get_client(client_id: str, user_id: str = "default-user", _token: str = Depends(verify_token)):
    store = get_gigsim_store()
    try:
        store.check_rate_limit(user_id)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return store.get_client_history(client_id)


@app.get("/market-stats")
def market_stats(skills: str = "", user_id: str = "default-user", _token: str = Depends(verify_token)):
    store = get_gigsim_store()
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    return store.get_market_stats(skill_list)


@app.get("/connects/{user_id}")
def connects_balance(user_id: str, _token: str = Depends(verify_token)):
    return get_gigsim_store().get_connects_balance(user_id)


@app.post("/proposals/draft")
def create_draft(req: DraftRequest, _token: str = Depends(verify_token)):
    store = get_gigsim_store()
    try:
        store.check_rate_limit(req.user_id)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return store.create_proposal_draft(
        user_id=req.user_id,
        job_id=req.job_id,
        cover_letter=req.cover_letter,
        bid_amount_usd=req.bid_amount_usd,
        screening_answers=req.screening_answers,
        idempotency_key=req.idempotency_key,
        dry_run=req.dry_run,
    )


@app.post("/proposals/submit")
def submit_proposal(req: SubmitRequest, _token: str = Depends(verify_token)):
    store = get_gigsim_store()
    try:
        return store.submit_proposal(
            user_id=req.user_id,
            draft_id=req.draft_id,
            idempotency_key=req.idempotency_key,
            dry_run=req.dry_run,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/messages/{job_id}")
def list_messages(job_id: str, _token: str = Depends(verify_token)):
    return {"messages": get_gigsim_store().list_messages(job_id)}


@app.post("/messages/send")
def send_message(req: MessageRequest, _token: str = Depends(verify_token)):
    return get_gigsim_store().send_message(
        user_id=req.user_id,
        job_id=req.job_id,
        text=req.text,
        idempotency_key=req.idempotency_key,
        dry_run=req.dry_run,
    )
