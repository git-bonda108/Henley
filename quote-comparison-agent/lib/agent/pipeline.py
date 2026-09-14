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
    "Extracting line items (Builder)",
    "Fetching competitor home design",
    "Fetching Builder home design",
    "Matching ranges and aligning items",
    "Scanning for ambiguity",
    "Ambiguity confirmation",
    "Composing comparison",
    "Generating summary",
]

AGENT_NARRATION = [
    "Orchestrator: G'day — two quotes in the tray. Righto, let's get cracking.",
    "Competitor Extractor: having a proper squiz at their PDF — every price gets a page and a verbatim snippet, no exceptions.",
    "Builder Extractor: going line by line on ours — if it hasn't got evidence, it doesn't get a dollar.",
    "Scout: ducking out for the competitor's design page… (left it blank? No worries, we crack on without it.)",
    "Scout: same again for the Builder's design page — context helps, but it never invents a number.",
    "Alignment: matching like-for-like across two builders' lingo — 'face brickwork', meet 'brick veneer'.",
    "Flagger: 'downlights included' with no count? Yeah, nah — that one's off to a human before any total moves.",
    "Verifier (different model, on purpose): trust nothing, re-read everything — any figure I can't confirm gets benched as Unconfirmed.",
    "Calculator: pure Decimal, zero model maths — reconciling to the cent, mate.",
    "Reporter: writing it up so the consultant can defend every single number at the kitchen table.",
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
        _log(log_fn, "Demo mode — using representative Carlisle vs Builder fixture.", logs)
        return demo_extract(wizard)

    comp_pdf = extract_pdf_text(wizard["competitor_pdf"])
    hen_pdf = extract_pdf_text(wizard["builder_pdf"])
    _log(log_fn, f"Read {comp_pdf['page_count']} pages from competitor PDF.", logs)
    _log(log_fn, f"Read {hen_pdf['page_count']} pages from Builder PDF.", logs)

    def _safe_fetch(url, label):
        if not (url or "").strip():
            _log(log_fn, f"{label} design URL not provided — continuing without design context.", logs)
            return {}
        try:
            page = fetch_url(url)
            _log(log_fn, f"Fetched {label} design: {page.get('title', url)}", logs)
            return page
        except Exception as exc:  # graceful degradation: design context is optional
            _log(log_fn, f"{label} design fetch failed ({exc.__class__.__name__}) — continuing without design context.", logs)
            return {}

    comp_design = _safe_fetch(wizard.get("competitor_url"), "competitor")
    hen_design = _safe_fetch(wizard.get("builder_url"), "Builder")

    payload = {
        "competitor_quote": comp_pdf["text"][:40_000],
        "builder_quote": hen_pdf["text"][:40_000],
        "competitor_design": comp_design.get("text", "")[:15_000],
        "builder_design": hen_design.get("text", "")[:15_000],
        "competitor_brand": wizard.get("competitor_brand"),
        "region": wizard.get("region"),
    }

    _log(log_fn, "Extractors: both PDFs are with the model now — big documents take a minute or two, hang tight.", logs)
    raw = call_llm("extract", payload)
    _log(log_fn, "Extractors: back with structured line items — every price carries its page and snippet.", logs)
    if raw:
        return ExtractResult.model_validate(raw)
    return demo_extract(wizard)


def scan_ambiguities(extract: ExtractResult, log_fn: LogFn | None = None) -> list[AmbiguityFlag]:
    provider = get_provider()
    if provider == "demo":
        _log(log_fn, "Detected 'Downlights included' with no quantity — flagging for confirmation.", [])
        return demo_ambiguities()

    _log(log_fn, "Flagger: combing the aligned rows for anything vague — this is a full re-read, give it a moment.", [])
    raw = call_llm("ambiguity_scan", extract.model_dump())
    if not raw:
        return demo_ambiguities()

    flags = []
    items = raw if isinstance(raw, list) else raw.get("flags", [])
    for item in items:
        if not isinstance(item, dict):
            continue
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
            "Orchestrate Builder quote comparison. Call extract first, then scan, then summarize. "
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

    _l("Orchestrator: kicking off — ingestion first, then the chain runs in order.")
    extract = ingest(wizard, _l)
    _l(f"Competitor: {extract.competitor_plan} — ${extract.competitor_total or 'TBC'}")
    _l(f"Builder: {extract.builder_plan} — ${extract.builder_total or 'TBC'}")
    _l("Flagger: sweeping for ambiguous inclusions — anything vague gets pulled up, not papered over.")
    ambiguities = scan_ambiguities(extract, _l)
    if ambiguities:
        _l(f"Flagger: found {len(ambiguities)} item(s) that need a human call — pipeline holds here until you sort them.")
    else:
        _l("Flagger: all clear — nothing dodgy. Straight through to the summary.")
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
