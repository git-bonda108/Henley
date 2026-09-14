"""Unified LLM access — Anthropic primary, OpenAI fallback."""

from __future__ import annotations

import json
import os
from typing import Any

from lib.prompts.comparison_system import COMPARISON_SYSTEM_PROMPT


def get_provider() -> str:
    explicit = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    if explicit == "demo":
        return "demo"
    if explicit == "openai" and os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    return "demo"


def _parse_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def call_llm(mode: str, payload: dict[str, Any]) -> Any:
    provider = get_provider()
    if provider == "demo":
        return None  # caller uses demo_data

    user_msg = json.dumps({"mode": mode, **payload}, ensure_ascii=False)

    if provider == "anthropic":
        return _call_anthropic(user_msg)
    return _call_openai(user_msg)


def _call_anthropic(user_msg: str) -> Any:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=180.0, max_retries=1)
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    resp = client.messages.create(
        model=model,
        max_tokens=8192,
        system=COMPARISON_SYSTEM_PROMPT + "\nReturn VALID JSON ONLY.",
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text
    return _parse_json(text)


def _call_openai(user_msg: str) -> Any:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=180.0, max_retries=1)
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": COMPARISON_SYSTEM_PROMPT + "\nReturn VALID JSON ONLY."},
            {"role": "user", "content": user_msg},
        ],
    )
    return _parse_json(resp.choices[0].message.content or "{}")
