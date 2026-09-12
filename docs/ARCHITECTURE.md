# Architecture

A Streamlit multi-page application wrapping a linear LLM pipeline with one hard stop: ambiguous quote items must be resolved by a human before the final comparison is composed. Everything else in the design serves that gate.

## Component map

```
quote-comparison-agent/
├── streamlit_app.py            # Entry point: st.navigation over five pages, theme, session bootstrap
├── config.py                   # Loads .env before any page imports
├── components/
│   ├── session.py              # SESSION_DEFAULTS, session-id minting (QCP-<date>-<hex>), reset
│   └── brand.py                # CSS injection, hero, INTERNAL banner, confidence pills
├── pages/
│   ├── 1_Home.py               # Landing + principle cards
│   ├── 2_New_Comparison.py     # 4-section wizard: two PDFs, two URLs, run context
│   ├── 3_Processing.py         # Runs the pipeline once; timeline + log; routes to Review or Summary
│   ├── 4_Review.py             # Human-in-the-loop: one card per ambiguity flag
│   └── 5_Summary.py            # 9-section report + conditionals + exports
├── lib/
│   ├── agent/
│   │   ├── pipeline.py         # Orchestration: ingest, scan_ambiguities, generate_summary,
│   │   │                       #   run_pipeline_sync, run_openai_agents_pipeline
│   │   ├── llm.py              # Provider resolution + unified call_llm(mode, payload)
│   │   └── demo_data.py        # Offline fixtures incl. the canonical downlights case
│   ├── ingestion/
│   │   ├── pdf.py              # pypdf text extraction, brand detection heuristic
│   │   └── webfetch.py         # Tavily Extract or httpx+BeautifulSoup, live per run
│   ├── prompts/
│   │   └── comparison_system.py  # Single system prompt with three output modes
│   ├── schema/
│   │   └── models.py           # Pydantic contracts: ExtractResult, AmbiguityFlag,
│   │                           #   AmbiguityResolution, ComparisonSummary (+ sub-models)
│   └── export.py               # Markdown, DOCX (python-docx), PDF (reportlab)
└── theme/fusion5.css           # Brand stylesheet (naming retained from the engagement)
```

## Data flow, end to end

1. **Wizard (`2_New_Comparison.py`)** collects two quote PDFs (read into bytes immediately), two home-design URLs, region, sales rep, and promotion checkboxes into `st.session_state.wizard`. Uploading a competitor PDF runs `detect_brand()` — a substring heuristic over extracted text — to pre-select the competitor radio group.
2. **Processing (`3_Processing.py`)** calls `run_pipeline(wizard)` exactly once per session (guarded by `processing_complete` / `ingest_result` flags, since Streamlit re-executes the script on every interaction).
3. **Ingest (`pipeline.ingest`)** extracts text from both PDFs (`pypdf`, capped at 120k chars), fetches both design URLs live, then sends one JSON payload (competitor quote 40k cap, company quote 40k, each design page 15k) to `call_llm("extract", …)`. The response is validated into `ExtractResult`.
4. **Ambiguity scan (`pipeline.scan_ambiguities`)** sends the full `ExtractResult` to `call_llm("ambiguity_scan", …)`; each returned flag gets a UUID if missing and is validated into `AmbiguityFlag`.
5. **Human review (`4_Review.py`)** presents flags one at a time. For each, the reviewer chooses: treat as comparable, flag as discussion point, or supply the competitor quantity. Resolutions accumulate in `resolved_ambiguities`. This is the pipeline's pause state — steps 9–10 of the visible timeline do not run until review completes. If the scan returns no flags, the pipeline skips straight to summary.
6. **Summary (`pipeline.generate_summary`)** sends wizard context, the extract, and the resolutions to `call_llm("summary", …)`, validated into `ComparisonSummary` — a 9-section schema (header, headline snapshot, design differences, inclusion matrix, value advantages, gaps, quote reconciliation, flagged items, open questions) plus five conditional sections.
7. **Render and export (`5_Summary.py`, `lib/export.py`)** — collapsible sections with an always-visible "INTERNAL — Sales team review required" banner, a "show source evidence" toggle, and PDF/DOCX/Markdown downloads.

## Orchestration analysis

**Sequential by design.** Extract → scan → summary is a strict dependency chain: the scan consumes the validated extract, and the summary consumes the extract *plus human resolutions*. Nothing in the chain is parallelisable without breaking the gate. The four ingestion I/O calls (2 PDFs, 2 URLs) run sequentially inside `ingest`; they are independent and could fan out, but at 2 PDFs + 2 pages per run the win is small (see Extending).

**One async island.** The only `asyncio` use is `run_openai_agents_pipeline`, because `Runner.run` from the OpenAI Agents SDK is async. `run_pipeline` bridges it with `asyncio.run()` and falls back to the sync path on any exception or if the SDK is not importable. In this mode a single manager agent ("call extract first, then scan, then summarize; never fabricate numbers; return structured JSON from tools only") orchestrates the same three functions exposed as `@function_tool`s; results are captured out-of-band in holder dicts rather than parsed from the agent's transcript, so tool outputs — not model prose — remain the source of truth.

**Three-tier provider resolution** (`llm.get_provider`): explicit `LLM_PROVIDER` wins; otherwise Anthropic key, then OpenAI key, then demo. Every pipeline step additionally degrades to fixtures if the LLM returns nothing parseable — the app never dead-ends on a provider failure, at the cost of silently showing fixture data (flagged honestly in EVALUATION.md).

**The UI timeline is presentational.** `3_Processing.py` animates ten named steps with `time.sleep` while the real pipeline runs as three calls; the "live log" renders callback-collected lines after the fact, not a token stream.

## State and context engineering

- **Session store:** Streamlit `st.session_state`, seeded from `SESSION_DEFAULTS` (wizard inputs, pipeline outputs as `model_dump()` dicts, review cursor, completion flags). Pydantic models are re-validated on read (`model_validate`) rather than stored as live objects — cheap insurance against Streamlit's rerun/pickling semantics.
- **Isolation:** each comparison mints a fresh `QCP-YYYY-MM-DD-XXXXXXXX` id; "New comparison" resets the whole state map. Nothing is written to disk or shared across sessions. `SESSION_TTL_MINUTES` exists in `.env.example` but no sweep implements it — state lives and dies with the Streamlit session.
- **Context assembly:** one system prompt (~40 lines) declares the agent's role, eight absolute anti-fabrication rules, and three output modes; the user message is a single JSON object with a `mode` discriminator. Later steps receive *structured* prior outputs (`extract.model_dump()`), never raw PDF text again — the extraction step is the only place raw documents enter the context.
- **Context bounds:** hard character caps at every ingress (PDF 120k at extraction, 40k into the prompt; web text 25k at fetch, 15k into the prompt). Crude but deterministic; nothing unbounded reaches the model.
- **Output contract:** `_parse_json` strips markdown fences; the OpenAI path additionally requests `response_format={"type": "json_object"}`. Pydantic validation is the real wall — an LLM response that does not fit the schema raises rather than rendering.

## Design decisions and trade-offs visible in the code

1. **Human gate over autonomy.** The system prompt forbids estimating; the pipeline *structurally* pauses when flags exist. The anti-fabrication stance is prompt-level *and* workflow-level, which is the right belt-and-braces for a tool whose failure mode is a sales rep quoting a wrong number to a customer.
2. **Demo-first resilience.** Fixture fallbacks at every step make the app demonstrable with zero keys and immune to provider outages — appropriate for a demonstration build, but production would need failures to be loud (see HARDENING.md).
3. **Schemas as the spine.** All cross-step and cross-page data moves through Pydantic models; the UI, exports, and prompts all target the same `ComparisonSummary` shape. Adding a section means one schema field, one renderer, one prompt line.
4. **Floats, not Decimals.** Money is `float | None` throughout, and arithmetic-bearing fields (subtotals, reconciled totals, `headline_advantage`) are produced by the LLM or fixtures, not computed in Python. For a demo this is tolerable; it is the first thing to fix for production (below).
5. **No streaming.** Simpler Streamlit code at the cost of the narrated-log illusion being post-hoc.

## Extending this system

Grounded next steps the current structure makes cheap:

1. **Deterministic reconciliation.** `QuoteReconciliation` already separates rows from subtotals — compute subtotals, reconciled totals, and `headline_advantage` in Python (`Decimal`) from validated `LineItem` and resolution data, and demote the LLM's numbers to advisory. This closes the last fabrication channel the prompt cannot: arithmetic.
2. **Unify the two execution modes.** `run_openai_agents_pipeline` currently generates its summary with an empty resolutions list and serialises only the first ambiguity flag from its scan tool — the human gate effectively exists only on the sync path. Make the manager agent halt at the scan step and resume after review, sharing the sync path's pause semantics behind one `run_pipeline` interface.
3. **Golden regression suite from the fixtures.** `demo_data.py` is already a hand-built golden case (extract, flags, summary for the downlights scenario). Lift it into `tests/` as the seed of the harness specified in EVALUATION.md before adding any new behaviour.
4. **True streaming narration.** The processing page's log list and callback plumbing (`LogFn`) are in place; swapping `client.messages.create` for the Anthropic streaming API and writing deltas into the existing `st.status` block turns the simulated timeline into a real one.
5. **Vision fallback for image-only PDFs.** `extract_pdf_text` returns empty text for scanned quotes and the pipeline proceeds anyway. The provider abstraction in `llm.py` is the natural seam for a rasterise-and-vision path gated on empty text extraction.
