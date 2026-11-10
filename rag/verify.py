"""Claim splitting and evidence grounding verification (Part B3 & R5)."""

from __future__ import annotations

import re
from typing import Any

from rag.variants.base import tokenize


def split_into_claims(text: str) -> list[str]:
    """Split proposal cover letter into atomic factual/experience claims."""
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [s.strip() for s in raw_sentences if len(s.strip()) > 12]


def verify_claim(claim: str, evidence_items: list[dict[str, Any]]) -> dict[str, Any]:
    """Check whether a single sentence claim is supported, partly_supported, or unsupported."""
    cited_ids = re.findall(r"\[([a-zA-Z0-9_-]+)\]", claim)
    ev_by_id = {e["evidence_id"]: e for e in evidence_items}

    # If the claim cites an evidence ID that was deleted or never retrieved -> unsupported!
    if cited_ids:
        valid_cited = [eid for eid in cited_ids if eid in ev_by_id]
        if not valid_cited:
            return {
                "claim": claim,
                "status": "unsupported",
                "matched_evidence_ids": [],
                "reason": f"Cited evidence {cited_ids} not found in retrieved portfolio items.",
            }
        # Check token overlap with cited evidence
        claim_tokens = set(tokenize(claim)) - {"i", "the", "a", "an", "for", "and", "to", "in", "of", "with"}
        best_overlap = 0.0
        for eid in valid_cited:
            ev = ev_by_id[eid]
            ev_tokens = set(tokenize(f"{ev.get('title', '')} {ev.get('text', '')} {' '.join(ev.get('skills', []))}"))
            overlap = len(claim_tokens & ev_tokens) / max(1, len(claim_tokens))
            best_overlap = max(best_overlap, overlap)
        if best_overlap >= 0.25:
            return {
                "claim": claim,
                "status": "supported",
                "matched_evidence_ids": valid_cited,
                "reason": "Backed by cited portfolio evidence.",
            }
        return {
            "claim": claim,
            "status": "partly_supported",
            "matched_evidence_ids": valid_cited,
            "reason": "Cited evidence exists but has partial lexical overlap.",
        }

    # Uncited sentences: check if it's a pure greeting/CTA or an ungrounded experience claim
    lower = claim.lower()
    is_cta_or_greeting = any(
        kw in lower for kw in ["hello", "hi ", "happy to", "let's", "available", "looking forward", "proposed bid", "best regards", "thanks", "interested in", "discuss your requirements"]
    )
    if is_cta_or_greeting and not any(kw in lower for kw in ["years", "built", "delivered", "achieved", "reduced", "improved"]):
        return {
            "claim": claim,
            "status": "supported",
            "matched_evidence_ids": [],
            "reason": "Conversational framing / call to action (no factual claim).",
        }

    # Check against all retrieved evidence
    claim_tokens = set(tokenize(claim)) - {"i", "the", "a", "an", "for", "and", "to", "in", "of", "with"}
    best_id = None
    best_overlap = 0.0
    for ev in evidence_items:
        ev_tokens = set(tokenize(f"{ev.get('title', '')} {ev.get('text', '')} {' '.join(ev.get('skills', []))}"))
        overlap = len(claim_tokens & ev_tokens) / max(1, len(claim_tokens))
        if overlap > best_overlap:
            best_overlap = overlap
            best_id = ev["evidence_id"]

    if best_overlap >= 0.40 and best_id:
        return {
            "claim": claim,
            "status": "partly_supported",
            "matched_evidence_ids": [best_id],
            "reason": f"Matches {best_id} but lacks explicit citation.",
        }

    return {
        "claim": claim,
        "status": "unsupported",
        "matched_evidence_ids": [],
        "reason": "No supporting portfolio evidence found for this claim.",
    }


def verify_and_rewrite_proposal(
    cover_letter: str,
    evidence_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify all claims and remove/rewrite unsupported claims before Critic."""
    claims = split_into_claims(cover_letter)
    results = [verify_claim(c, evidence_items) for c in claims]
    unsupported_before = sum(1 for r in results if r["status"] == "unsupported")

    kept_sentences = []
    for r in results:
        if r["status"] == "supported":
            kept_sentences.append(r["claim"])
        elif r["status"] == "partly_supported":
            eid = r["matched_evidence_ids"][0] if r["matched_evidence_ids"] else ""
            if eid and f"[{eid}]" not in r["claim"]:
                kept_sentences.append(f"{r['claim'].rstrip('.')} [{eid}].")
            else:
                kept_sentences.append(r["claim"])
        # unsupported claims are removed!

    cleaned_letter = " ".join(kept_sentences).strip()
    if not cleaned_letter:
        cleaned_letter = "I am interested in your project and would be glad to discuss your requirements in detail."

    post_results = [verify_claim(c, evidence_items) for c in split_into_claims(cleaned_letter)]
    unsupported_after = sum(1 for r in post_results if r["status"] == "unsupported")

    return {
        "cleaned_cover_letter": cleaned_letter,
        "claim_results": results,
        "unsupported_before": unsupported_before,
        "unsupported_after": unsupported_after,
        "total_claims": len(results),
    }
