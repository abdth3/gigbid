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


# Serve built React frontend in production/single-host mode with SPA fallback
from fastapi.responses import FileResponse

WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
if WEB_DIST.exists():
    assets_dir = WEB_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        candidate = WEB_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(WEB_DIST / "index.html"))
