"""Settings, autonomy, budgets, saved searches, and Long-Term Memory viewer/delete routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from agent.llm_router import load_config
from agent.memory.store import get_memory_store
from apps.api.auth.security import USERS, get_current_user
from apps.api.schemas.models import SettingsUpdateRequest
from apps.api.state_store import get_api_store

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings(user: dict = Depends(get_current_user)):
    cfg = load_config()
    memories = get_memory_store().list_memories(user["user_id"])
    api_store = get_api_store()
    return {
        "autonomy_level": user.get("autonomy_level", "manual_approve"),
        "weekly_connects_budget": user.get("weekly_connects_budget", 60),
        "marketplace_mode": cfg.get("marketplace", {}).get("mode", "gigsim"),
        "rag_variant": cfg.get("rag", {}).get("variant", "v4_outcome"),
        "budgets": cfg.get("budgets", {}),
        "saved_searches": api_store.saved_searches.get(user["user_id"], ["LangGraph FastAPI", "React TypeScript"]),
        "memory": memories,
    }


@router.put("")
def update_settings(req: SettingsUpdateRequest, user: dict = Depends(get_current_user)):
    u = USERS[user["user_id"]]
    u["autonomy_level"] = req.autonomy_level
    u["weekly_connects_budget"] = req.weekly_connects_budget
    api_store = get_api_store()
    api_store.saved_searches[user["user_id"]] = req.saved_searches
    api_store.save()
    return {"status": "updated"}


@router.delete("/memory/{memory_type}/{item_id}")
def delete_memory_item(memory_type: str, item_id: str, user: dict = Depends(get_current_user)):
    if memory_type not in {"style_memory", "outcome_memory"}:
        raise HTTPException(status_code=400, detail="Invalid memory type")
    ok = get_memory_store().delete_memory(user["user_id"], memory_type, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"status": "deleted", "id": item_id}
