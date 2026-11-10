"""Portfolio & GitHub ingestion loader with incremental re-indexing and deletion."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
PERSONAS_DIR = ROOT / "data" / "personas"


@dataclass
class PortfolioChunk:
    chunk_id: str
    evidence_id: str
    persona: str
    type: str  # case_study | repo | review | past_proposal | cv
    project: str
    title: str
    text: str
    skills: list[str] = field(default_factory=list)
    date: str = ""
    client_industry: str = ""
    outcome: str = ""
    source: str = ""
    sub_view: str = "summary"  # summary | readme | code (for V5 multi-vector)


class PortfolioCorpusStore:
    """In-memory corpus store supporting incremental additions and deletions."""

    def __init__(self) -> None:
        self.chunks_by_persona: dict[str, list[PortfolioChunk]] = {}
        self._loaded = False

    def load_all(self, force: bool = False) -> None:
        if self._loaded and not force:
            return
        self.chunks_by_persona.clear()
        if not PERSONAS_DIR.exists():
            self._loaded = True
            return

        for pdir in PERSONAS_DIR.iterdir():
            if not pdir.is_dir():
                continue
            persona = pdir.name
            chunks: list[PortfolioChunk] = []

            # 1. Portfolio items (case studies + repos)
            p_items_path = pdir / "portfolio_items.json"
            if p_items_path.exists():
                items = json.loads(p_items_path.read_text(encoding="utf-8"))
                for it in items:
                    ev_id = it["evidence_id"]
                    chunks.append(
                        PortfolioChunk(
                            chunk_id=f"{ev_id}::summary",
                            evidence_id=ev_id,
                            persona=persona,
                            type=it.get("type", "case_study"),
                            project=it.get("title", ""),
                            title=it.get("title", ""),
                            text=f"{it.get('title', '')}. {it.get('summary', '')} Outcome: {it.get('outcome', '')}",
                            skills=it.get("skills", []),
                            date=it.get("date", ""),
                            client_industry=it.get("industry", ""),
                            outcome=it.get("outcome", ""),
                            source=it.get("source", ""),
                            sub_view="summary",
                        )
                    )

            # 2. Markdown case studies (code + prose chunks for V5)
            cs_dir = pdir / "case_studies"
            if cs_dir.exists():
                for md_file in cs_dir.glob("*.md"):
                    ev_id = md_file.stem
                    content = md_file.read_text(encoding="utf-8")
                    code_blocks = re.findall(r"```python\n(.*?)```", content, flags=re.S)
                    if code_blocks:
                        chunks.append(
                            PortfolioChunk(
                                chunk_id=f"{ev_id}::code",
                                evidence_id=ev_id,
                                persona=persona,
                                type="case_study",
                                project=ev_id,
                                title=f"{ev_id} code",
                                text=code_blocks[0],
                                skills=self._extract_skills_from_md(content),
                                source=str(md_file.relative_to(ROOT)),
                                sub_view="code",
                            )
                        )

            # 3. Repo READMEs & code (simulating GitHub MCP ingestion)
            repos_dir = pdir / "repos"
            if repos_dir.exists():
                for rfile in repos_dir.iterdir():
                    if rfile.suffix == ".md":
                        ev_id = rfile.stem.replace("_README", "")
                        chunks.append(
                            PortfolioChunk(
                                chunk_id=f"{ev_id}::readme",
                                evidence_id=ev_id,
                                persona=persona,
                                type="repo",
                                project=ev_id,
                                title=f"README {ev_id}",
                                text=rfile.read_text(encoding="utf-8"),
                                source=f"github://abdth3/{ev_id}",
                                sub_view="readme",
                            )
                        )
                    elif rfile.suffix == ".py":
                        ev_id = rfile.stem
                        chunks.append(
                            PortfolioChunk(
                                chunk_id=f"{ev_id}::code",
                                evidence_id=ev_id,
                                persona=persona,
                                type="repo",
                                project=ev_id,
                                title=f"Code {ev_id}",
                                text=rfile.read_text(encoding="utf-8"),
                                source=f"github://abdth3/{ev_id}",
                                sub_view="code",
                            )
                        )

            # 4. Reviews
            rev_path = pdir / "reviews.json"
            if rev_path.exists():
                for r in json.loads(rev_path.read_text(encoding="utf-8")):
                    chunks.append(
                        PortfolioChunk(
                            chunk_id=f"{r['review_id']}::review",
                            evidence_id=r["review_id"],
                            persona=persona,
                            type="review",
                            project=r.get("project", ""),
                            title=f"Client Review ({r.get('rating', 5.0)}★): {r.get('project', '')}",
                            text=r.get("text", ""),
                            skills=r.get("skills", []),
                            date=r.get("date", ""),
                            client_industry=r.get("industry", ""),
                            outcome=f"rating_{r.get('rating', 5.0)}",
                            source=f"data/personas/{persona}/reviews.json",
                        )
                    )

            # 5. Past proposals with outcomes
            prop_path = pdir / "past_proposals.json"
            if prop_path.exists():
                for p in json.loads(prop_path.read_text(encoding="utf-8")):
                    chunks.append(
                        PortfolioChunk(
                            chunk_id=f"{p['proposal_id']}::proposal",
                            evidence_id=p["proposal_id"],
                            persona=persona,
                            type="past_proposal",
                            project=p.get("project", ""),
                            title=f"Past Proposal ({p.get('outcome', 'ignored')}): {p.get('project', '')}",
                            text=p.get("text", ""),
                            skills=p.get("skills", []),
                            date=p.get("date", ""),
                            client_industry=p.get("industry", ""),
                            outcome=p.get("outcome", "ignored"),
                            source=f"data/personas/{persona}/past_proposals.json",
                        )
                    )

            self.chunks_by_persona[persona] = chunks
        self._loaded = True

    @staticmethod
    def _extract_skills_from_md(text: str) -> list[str]:
        m = re.search(r"\*\*Skills:\*\*\s*(.+)", text)
        if not m:
            return []
        return [s.strip() for s in m.group(1).split(",") if s.strip()]

    def get_chunks(self, persona: str) -> list[PortfolioChunk]:
        self.load_all()
        return list(self.chunks_by_persona.get(persona, []))

    def add_evidence(self, persona: str, item: dict[str, Any]) -> PortfolioChunk:
        self.load_all()
        ev_id = item.get("evidence_id") or f"{persona}-custom-{len(self.chunks_by_persona.get(persona, [])) + 1}"
        chunk = PortfolioChunk(
            chunk_id=f"{ev_id}::summary",
            evidence_id=ev_id,
            persona=persona,
            type=item.get("type", "case_study"),
            project=item.get("title", "Custom Work"),
            title=item.get("title", "Custom Work"),
            text=item.get("summary", ""),
            skills=item.get("skills", []),
            date=item.get("date", "2026-11-10"),
            client_industry=item.get("industry", "SaaS"),
            outcome=item.get("outcome", "delivered"),
            source=item.get("source", "ui_upload"),
        )
        self.chunks_by_persona.setdefault(persona, []).append(chunk)
        return chunk

    def delete_evidence(self, persona: str, evidence_id: str) -> bool:
        self.load_all()
        existing = self.chunks_by_persona.get(persona, [])
        filtered = [c for c in existing if c.evidence_id != evidence_id]
        removed = len(filtered) < len(existing)
        self.chunks_by_persona[persona] = filtered
        return removed


_CORPUS_STORE = PortfolioCorpusStore()


def get_corpus_store() -> PortfolioCorpusStore:
    return _CORPUS_STORE
