"""GigBid FastAPI Application."""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apps.api.routers import analytics, auth, jobs, messages, proposals, runs, settings

app = FastAPI(
    title="GigBid Multi-Agent Freelancer Copilot API",
    version="1.0.0",
    description="LangGraph multi-agent system with MCP servers, Advanced RAG, and human-in-the-loop approvals.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(proposals.router)
app.include_router(messages.router)
app.include_router(runs.router)
app.include_router(analytics.router)
app.include_router(settings.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gigbid-api"}


# Serve built React frontend in production/single-host mode if present
WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
