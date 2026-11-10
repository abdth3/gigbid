"""Explicit promotion rules for long-term memory (C2 & R7).

Raw tool output NEVER goes straight into long-term memory.
Only promoted knowledge passes through these deterministic rules:
1. Style Memory: promoted when a human edit removes a repeated phrase (>=1 edit diff)
   or explicitly shortens/rewrites an opening.
2. Outcome Memory: promoted when a submitted proposal receives a verified outcome
   ('won' or 'replied') with a recorded strategy and job category.
"""

from __future__ import annotations

import difflib
from typing import Any


def extract_style_rule_from_diff(original: str, edited: str) -> list[dict[str, str]]:
    """Promote actionable style rules from a user's diff on a proposal draft."""
    rules: list[dict[str, str]] = []
    orig_lower = original.lower()
    edit_lower = edited.lower()

    banned_phrases = [
        "passionate",
        "dear sir/madam",
        "excited to apply",
        "i am confident",
        "100% guarantee",
        "best regards",
    ]
    for phrase in banned_phrases:
        if phrase in orig_lower and phrase not in edit_lower:
            rules.append({
                "rule_type": "avoid_phrase",
                "rule": f"Never say '{phrase}'",
                "source": "user_edit_diff",
            })

    # Check if user cut the first sentence
    orig_sentences = [s.strip() for s in original.split(".") if s.strip()]
    edit_sentences = [s.strip() for s in edited.split(".") if s.strip()]
    if len(orig_sentences) >= 2 and edit_sentences and orig_sentences[0] not in edited:
        if len(edit_sentences) < len(orig_sentences):
            rules.append({
                "rule_type": "structure",
                "rule": "Always cut generic first sentence and lead with evidence",
                "source": "user_edit_diff",
            })

    # Check if user significantly shortened the draft
    if len(edited) < len(original) * 0.80 and len(edited) > 50:
        rules.append({
            "rule_type": "conciseness",
            "rule": "Keep cover letter concise (< 900 chars) with bulleted metrics",
            "source": "user_edit_diff",
        })

    return rules


def should_promote_outcome(outcome: str, category: str, strategy: str) -> dict[str, Any] | None:
    """Only promote verified 'won' or 'replied' outcomes into outcome memory."""
    if outcome not in {"won", "replied"}:
        return None
    return {
        "category": category,
        "strategy": strategy,
        "outcome": outcome,
        "rule": f"Strategy '{strategy}' achieved '{outcome}' in category '{category}'",
        "source": "verified_outcome_promotion",
    }
