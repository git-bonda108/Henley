"""
Agent orchestration — OpenAI Agents SDK (fallback) + direct pipeline.

Architecture (per FRD / SDD):
  Manager pattern: extract → ambiguity_scan → [human review] → summary

Anthropic path: sequential LLM calls with structured JSON modes.
OpenAI path: OpenAI Agents SDK with specialist agents exposed as tools.
Demo path: rich fixtures including canonical downlights case.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from lib.agent.demo_data import demo_ambiguities, demo_extract, demo_summary
from lib.agent.llm import call_llm, get_provider
from lib.ingestion.pdf import extract_pdf_text
from lib.ingestion.webfetch import fetch_url
from lib.schema.models import AmbiguityFlag, ComparisonSummary, ExtractResult


LogFn = Callable[[str], None]

PIPELINE_STEPS = [
    "Ingesting documents",
    "Extracting line items (competitor)",
    "Extracting line items (Henley)",
    "Fetching competitor home design",
    "Fetching Henley home design",
    "Matching ranges and aligning items",
    "Scanning for ambiguity",
    "Ambiguity confirmation",
    "Composing comparison",
    "Generating summary",
]


@dataclass
class PipelineResult:
    extract: ExtractResult
    ambiguities: list[AmbiguityFlag] = field(default_factory=list)
    summary: ComparisonSummary | None = None
    logs: list[str] = field(default_factory=list)


def _log(log_fn: LogFn | None, msg: str, bucket: list[str]) -> None:
    bucket.append(msg)
    if log_fn:
        log_fn(msg)


def ingest(wizard: dict, log_fn: LogFn | None = None) -> ExtractResult:
    logs: list[str] = []
    provider = get_provider()

    if provider == "demo" or not wizard.get("competitor_pdf"):
        _log(log_fn, "Demo mode — using representative Carlisle vs Henley fixture.", logs)
        return demo_extract(wizard)

    comp_pdf = extract_pdf_text(wizard["competitor_pdf"])
    hen_pdf = extract_pdf_text(wizard["henley_pdf"])
    _log(log_fn, f"Read {comp_pdf['page_count']} pages from competitor PDF.", logs)
    _log(log_fn, f"Read {hen_pdf['page_count']} pages from Henley PDF.", logs)

    comp_design = fetch_url(wizard["competitor_url"])
    hen_design = fetch_url(wizard["henley_url"])
    _log(log_fn, f"Fetched competitor design: {comp_design.get('title', wizard['competitor_url'])}", logs)
    _log(log_fn, f"Fetched Henley design: {hen_design.get('title', wizard['henley_url'])}", logs)

    payload = {
        "competitor_quote": comp_pdf["text"][:40_000],
        "henley_quote": hen_pdf["text"][:40_000],
        "competitor_design": comp_design.get("text", "")[:15_000],
        "henley_design": hen_design.get("text", "")[:15_000],
        "competitor_brand": wizard.get("competitor_brand"),
        "region": wizard.get("region"),
    }

    raw = call_llm("extract", payload)
    if raw:
        return ExtractResult.model_validate(raw)
    return demo_extract(wizard)


def scan_ambiguities(extract: ExtractResult, log_fn: LogFn | None = None) -> list[AmbiguityFlag]:
    provider = get_provider()
    if provider == "demo":
        _log(log_fn, "Detected 'Downlights included' with no quantity — flagging for confirmation.", [])
        return demo_ambiguities()

    raw = call_llm("ambiguity_scan", extract.model_dump())
    if not raw:
        return demo_ambiguities()

    flags = []
    items = raw if isinstance(raw, list) else raw.get("flags", [])
    for item in items:
        item.setdefault("id", str(uuid.uuid4()))
        flags.append(AmbiguityFlag.model_validate(item))
    return flags


def generate_summary(
    wizard: dict,
    extract: ExtractResult,
    resolved: list[dict],
    log_fn: LogFn | None = None,
) -> ComparisonSummary:
    provider = get_provider()
    if provider == "demo":
        _log(log_fn, "Composing internal summary from resolved ambiguities.", [])
        return demo_summary(wizard, resolved)

    raw = call_llm(
        "summary",
        {
            "wizard": wizard,
            "extract": extract.model_dump(),
            "resolved_ambiguities": resolved,
        },
    )
    if raw:
        return ComparisonSummary.model_validate(raw)
    return demo_summary(wizard, resolved)


async def run_openai_agents_pipeline(wizard: dict) -> PipelineResult:
    """OpenAI Agents SDK — manager orchestrates extract / scan / summary specialists."""
    import os

    try:
        from agents import Agent, Runner, function_tool
    except ImportError:
        return run_pipeline_sync(wizard)

    if get_provider() != "openai":
        return run_pipeline_sync(wizard)

    logs: list[str] = []
    extract_holder: dict[str, Any] = {}
    ambiguity_holder: dict[str, Any] = {}
    summary_holder: dict[str, Any] = {}

    @function_tool
    def tool_extract() -> str:
        result = ingest(wizard, lambda m: logs.append(m))
        extract_holder["data"] = result
        return result.model_dump_json()

    @function_tool
    def tool_scan() -> str:
        ex = extract_holder.get("data") or ingest(wizard)
        flags = scan_ambiguities(ex, lambda m: logs.append(m))
        ambiguity_holder["data"] = flags
        return AmbiguityFlag.model_validate(flags[0]).model_dump_json() if flags else "[]"

    @function_tool
    def tool_summarize() -> str:
        ex = extract_holder.get("data") or ingest(wizard)
        summary = generate_summary(wizard, ex, [], lambda m: logs.append(m))
        summary_holder["data"] = summary
        return summary.model_dump_json()

    manager = Agent(
        name="Quote Comparison Manager",
        instructions=(
            "Orchestrate Henley quote comparison. Call extract first, then scan, then summarize. "
            "Never fabricate numbers. Return structured JSON from tools only."
        ),
        tools=[
            tool_extract,
            tool_scan,
            tool_summarize,
        ],
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    )

    await Runner.run(
        manager,
        "Run full comparison pipeline for the uploaded quotes. Use tools in order.",
    )

    ex = extract_holder.get("data") or demo_extract(wizard)
    amb = ambiguity_holder.get("data") or demo_ambiguities()
    summ = summary_holder.get("data")

    return PipelineResult(extract=ex, ambiguities=amb, summary=summ, logs=logs)


def run_pipeline_sync(wizard: dict, log_fn: LogFn | None = None) -> PipelineResult:
    logs: list[str] = []

    def _l(m: str) -> None:
        _log(log_fn, m, logs)

    _l("Starting document ingestion…")
    extract = ingest(wizard, _l)
    _l(f"Competitor: {extract.competitor_plan} — ${extract.competitor_total or 'TBC'}")
    _l(f"Henley: {extract.henley_plan} — ${extract.henley_total or 'TBC'}")
    _l("Scanning for ambiguous inclusions…")
    ambiguities = scan_ambiguities(extract, _l)
    if ambiguities:
        _l(f"Found {len(ambiguities)} item(s) requiring human confirmation.")
    else:
        _l("No ambiguities detected — proceeding to summary.")
        summary = generate_summary(wizard, extract, [], _l)
        return PipelineResult(extract=extract, ambiguities=[], summary=summary, logs=logs)

    return PipelineResult(extract=extract, ambiguities=ambiguities, logs=logs)


def run_pipeline(wizard: dict, log_fn: LogFn | None = None) -> PipelineResult:
    if get_provider() == "openai":
        try:
            return asyncio.run(run_openai_agents_pipeline(wizard))
        except Exception:
            pass
    return run_pipeline_sync(wizard, log_fn)
