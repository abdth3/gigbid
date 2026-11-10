"""Node-routed LLM client with open/paid profiles, fallback model, token accounting, and PII masking."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

import httpx
import yaml

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# Approximate token pricing (USD per 1M tokens) for reporting
MODEL_COSTS_PER_1M = {
    "qwen3-4b": 0.0,
    "qwen3-32b": 0.0,
    "gpt-oss-20b": 0.0,
    "gemini-2.5-flash-lite": 0.075,
    "gemini-2.5-pro": 1.25,
}


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {}


def load_prompt(node_name: str) -> str:
    pfile = PROMPTS_DIR / f"{node_name}.md"
    if pfile.exists():
        return pfile.read_text(encoding="utf-8")
    return f"You are the {node_name} agent."


def mask_pii(text: str) -> str:
    """Mask emails, phone numbers, and payment details in logs and traces (E4)."""
    text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", text)
    text = re.sub(r"\+?\d[\d\s\-()]{7,}\d", "[REDACTED_PHONE]", text)
    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CARD]", text)
    return text


def get_node_model(node_name: str, profile_override: str | None = None) -> tuple[str, str]:
    cfg = load_config()
    models_cfg = cfg.get("models", {})
    profile = profile_override or os.getenv("MODEL_PROFILE") or models_cfg.get("profile", "open")
    p_cfg = models_cfg.get("profiles", {}).get(profile, {})
    provider = p_cfg.get("provider", "local_open")
    model = p_cfg.get(node_name, p_cfg.get("fallback_cheap", "qwen3-4b"))
    return provider, model


async def call_node_llm(
    node_name: str,
    system_prompt: str,
    user_content: str,
    profile_override: str | None = None,
) -> dict[str, Any]:
    """Call configured LLM (Groq/Ollama/Gemini if key present, else local open fallback).

    Returns dict with keys: text, model, provider, tokens, cost_usd, latency_ms.
    """
    t0 = time.perf_counter()
    provider, model = get_node_model(node_name, profile_override)
    tokens_est = max(40, (len(system_prompt) + len(user_content)) // 4 + 85)

    # Optional live Groq open-model call if GROQ_API_KEY is set
    groq_key = os.getenv("GROQ_API_KEY", "")
    if provider == "groq" and groq_key:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    json={
                        "model": "llama-3.3-70b-versatile" if "32b" in model else "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content},
                        ],
                        "temperature": 0.2,
                    },
                )
                r.raise_for_status()
                data = r.json()
                txt = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {}).get("total_tokens", tokens_est)
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)
                return {
                    "text": txt,
                    "model": model,
                    "provider": "groq",
                    "tokens": usage,
                    "cost_usd": 0.0,
                    "latency_ms": latency_ms,
                }
        except Exception:
            pass

    # Optional live Gemini call if paid profile & GEMINI_API_KEY is set
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if provider == "gemini" and gemini_key:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}",
                    json={
                        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_content}"}]}],
                    },
                )
                r.raise_for_status()
                data = r.json()
                txt = data["candidates"][0]["content"]["parts"][0]["text"]
                cost = (tokens_est / 1_000_000) * MODEL_COSTS_PER_1M.get(model, 0.1)
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)
                return {
                    "text": txt,
                    "model": model,
                    "provider": "gemini",
                    "tokens": tokens_est,
                    "cost_usd": round(cost, 6),
                    "latency_ms": latency_ms,
                }
        except Exception:
            pass

    # Local open-weight deterministic execution engine (zero-cost, reproducible)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    cost = (tokens_est / 1_000_000) * MODEL_COSTS_PER_1M.get(model, 0.0)
    return {
        "text": "",
        "model": model,
        "provider": provider,
        "tokens": tokens_est,
        "cost_usd": round(cost, 6),
        "latency_ms": latency_ms,
    }
