"""Long-term memory store (Style Memory & Outcome Memory) backed by LangGraph Store + JSON persistence."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.store.memory import InMemoryStore

from agent.memory.promotion_rules import extract_style_rule_from_diff, should_promote_outcome

MEMORY_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "long_term_memory.json"


class GigBidMemoryStore:
    """Manages per-user style_memory and outcome_memory with explicit promotion rules."""

    def __init__(self) -> None:
        self.lg_store = InMemoryStore()
        self._load()

    def _load(self) -> None:
        if not MEMORY_FILE.exists():
            # Seed 2 initial realistic style rules so UI Memory Viewer is immediately populated
            self.add_style_rule("default-user", "Never say 'passionate' or 'Dear Sir/Madam'", "seeded_preference")
            self.add_style_rule("default-user", "Lead first sentence with measurable portfolio outcome", "seeded_preference")
            return
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        for ns_key, items in data.items():
            parts = tuple(ns_key.split("::"))
            for item_id, val in items.items():
                self.lg_store.put(parts, item_id, val)

    def _save(self) -> None:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Persist known namespaces
        dump: dict[str, dict[str, Any]] = {}
        for user_id in ("default-user", "reviewer", "abdullah"):
            for kind in ("style_memory", "outcome_memory"):
                ns = (user_id, kind)
                items = self.lg_store.search(ns)
                if items:
                    dump[f"{user_id}::{kind}"] = {it.key: it.value for it in items}
        MEMORY_FILE.write_text(json.dumps(dump, indent=2), encoding="utf-8")

    def add_style_rule(self, user_id: str, rule: str, source: str = "user_edit_diff") -> dict[str, Any]:
        ns = (user_id, "style_memory")
        existing = self.lg_store.search(ns)
        for it in existing:
            if it.value.get("rule") == rule:
                return it.value
        item_id = f"style-{uuid.uuid4().hex[:8]}"
        val = {
            "id": item_id,
            "rule": rule,
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.lg_store.put(ns, item_id, val)
        self._save()
        return val

    def promote_from_edit(self, user_id: str, original: str, edited: str) -> list[dict[str, Any]]:
        promoted = []
        for r in extract_style_rule_from_diff(original, edited):
            promoted.append(self.add_style_rule(user_id, r["rule"], r["source"]))
        return promoted

    def promote_outcome(self, user_id: str, outcome: str, category: str, strategy: str) -> dict[str, Any] | None:
        rule_obj = should_promote_outcome(outcome, category, strategy)
        if not rule_obj:
            return None
        ns = (user_id, "outcome_memory")
        item_id = f"outcome-{uuid.uuid4().hex[:8]}"
        val = {
            "id": item_id,
            **rule_obj,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.lg_store.put(ns, item_id, val)
        self._save()
        return val

    def list_memories(self, user_id: str = "default-user") -> dict[str, list[dict[str, Any]]]:
        return {
            "style_memory": [it.value for it in self.lg_store.search((user_id, "style_memory"))],
            "outcome_memory": [it.value for it in self.lg_store.search((user_id, "outcome_memory"))],
        }

    def delete_memory(self, user_id: str, memory_type: str, item_id: str) -> bool:
        ns = (user_id, memory_type)
        existing = self.lg_store.get(ns, item_id)
        if existing is None:
            return False
        self.lg_store.delete(ns, item_id)
        self._save()
        return True


_MEMORY_STORE: GigBidMemoryStore | None = None


def get_memory_store() -> GigBidMemoryStore:
    global _MEMORY_STORE
    if _MEMORY_STORE is None:
        _MEMORY_STORE = GigBidMemoryStore()
    return _MEMORY_STORE
