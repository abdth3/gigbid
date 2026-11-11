"""Unit tests for RAG variants, claim verification, memory promotion rules, and PII masking."""

from __future__ import annotations

from agent.llm_router import mask_pii
from agent.memory.promotion_rules import extract_style_rule_from_diff, should_promote_outcome
from rag.ingest.loader import get_corpus_store
from rag.retriever import retrieve_evidence
from rag.verify import verify_and_rewrite_proposal


def test_rag_variants_return_ranked_evidence():
    for var in ("v0_naive", "v1_decomp", "v2_hybrid", "v3_rerank", "v4_outcome", "v5_multivector", "v9_skill_graph"):
        items = retrieve_evidence("Python scikit-learn churn classification", persona="ai_ml_engineer", k=3, variant=var)
        assert len(items) > 0, f"Variant {var} returned no items"


def test_claim_verification_removes_unsupported_claims():
    ev = [{"evidence_id": "ai_ml_engineer-case-01", "title": "Customer Churn Prediction Pipeline", "text": "Reduced false negatives by 24% using Python scikit-learn", "skills": ["Python", "scikit-learn"]}]
    draft = "I delivered Customer Churn Prediction Pipeline [ai_ml_engineer-case-01]. I also have 10 years of Rust kernel experience."
    res = verify_and_rewrite_proposal(draft, ev)
    assert res["unsupported_before"] == 1
    assert res["unsupported_after"] == 0
    assert "Rust kernel" not in res["cleaned_cover_letter"]


def test_memory_promotion_rules():
    rules = extract_style_rule_from_diff(
        "Dear Sir/Madam, I am passionate about your project. I built X.",
        "I built X with 24% improvement.",
    )
    assert any("passionate" in r["rule"].lower() for r in rules)
    assert should_promote_outcome("ignored", "ai_ml", "evidence_first") is None
    assert should_promote_outcome("won", "ai_ml", "evidence_first") is not None


def test_pii_masking():
    masked = mask_pii("Email me at test.user@example.com or +1-555-123-4567")
    assert "test.user@example.com" not in masked
    assert "[REDACTED_EMAIL]" in masked
    assert "[REDACTED_PHONE]" in masked


def test_delete_evidence_and_reverify():
    store = get_corpus_store()
    store.load_all(force=True)
    added = store.add_evidence("ai_ml_engineer", {"evidence_id": "temp-ev-99", "title": "Temp Project", "summary": "Built temp pipeline"})
    assert added.evidence_id == "temp-ev-99"
    assert store.delete_evidence("ai_ml_engineer", "temp-ev-99") is True
    res = verify_and_rewrite_proposal("I built Temp Project [temp-ev-99].", [])
    assert res["unsupported_before"] == 1
    assert res["unsupported_after"] == 0
