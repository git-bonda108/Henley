# Evaluation

## What automated testing exists today

**None.** There are no test files, no test runner configuration, and no CI in this repository at HEAD (`.gitignore` anticipates a `.pytest_cache/`, but no suite was ever committed). Any statement about test counts or assertion coverage for this codebase would be unsupported. What the code *does* have is runtime verification:

- **Schema validation as the output gate.** Every LLM response is validated with Pydantic before use: `ExtractResult.model_validate(raw)` (`lib/agent/pipeline.py:85`), `AmbiguityFlag.model_validate(item)` (`pipeline.py:103`), `ComparisonSummary.model_validate(raw)` (`pipeline.py:127`). Enum-typed fields (`confidence: Literal["LOW","MEDIUM"]`, `advantage: Literal["builder","competitor","none"]`, resolution `action`) reject out-of-vocabulary model output.
- **Prompt-level rules** (`lib/prompts/comparison_system.py`): never fabricate, emit "Unconfirmed — requires manual validation" for missing values, flag unquantified inclusions as LOW-confidence before comparing, use only the four supplied materials.
- **A workflow-level gate**: when the ambiguity scan returns flags, the pipeline stops and the Review page requires a human resolution per flag before the summary step runs (sync path).

These are guardrails, not tests — nothing exercises them automatically.

## Edge cases the code visibly handles

Enumerated from the source, with locations:

| Case | Handling | Where |
|---|---|---|
| No API keys configured | Provider resolves to `demo`; full pipeline runs on fixtures | `llm.get_provider` |
| LLM returns nothing / unparseable envelope | Step falls back to demo fixtures instead of crashing | `pipeline.ingest/scan_ambiguities/generate_summary` |
| LLM wraps JSON in markdown fences | Fence stripping before `json.loads` | `llm._parse_json` |
| OpenAI Agents SDK not installed | `ImportError` → sync pipeline | `pipeline.run_openai_agents_pipeline` |
| Agents SDK run raises | Broad `except Exception` → sync pipeline | `pipeline.run_pipeline` |
| Malformed URL input | Scheme check raises `ValueError` before any request | `webfetch.fetch_url` |
| Slow/failed fetch | `httpx` timeouts (15s direct / 20s Tavily), `raise_for_status`, redirects followed | `webfetch` |
| Non-HTML response | Returned as truncated raw text rather than parsed | `webfetch.fetch_url` |
| Tavily returns no content | Explicit `ValueError` | `webfetch._fetch_tavily` |
| Oversized documents | Character caps at every boundary (120k/40k/25k/15k) | `pdf.py`, `pipeline.ingest`, `webfetch` |
| PDF pages with no text layer | `extract_text() or ""`, empty pages dropped from the join | `pdf.extract_pdf_text` |
| Flags missing an `id` | `setdefault("id", uuid4())` before validation | `pipeline.scan_ambiguities` |
| No ambiguities found | Pipeline skips review and composes the summary directly | `pipeline.run_pipeline_sync` |
| User lands on Processing/Summary without inputs | Guard + redirect to the wizard | `3_Processing.py`, `5_Summary.py` |
| Streamlit rerun re-triggering the pipeline | `processing_complete`/`ingest_result` idempotency guards | `3_Processing.py` |

## Known gaps (from reading the code, stated plainly)

- **Silent fixture substitution.** A production run whose LLM call fails degrades to demo data with no visible error — the strongest candidate for a loud failure path.
- **The Agents SDK mode bypasses the human gate.** `run_openai_agents_pipeline` summarises with `resolved=[]` and its scan tool serialises only the first flag; only the sync path enforces review-before-summary.
- **`except Exception: pass`** in `run_pipeline` hides the reason an Agents SDK run failed.
- **Arithmetic is model-produced.** Subtotals, reconciled totals, and the headline advantage are LLM/fixture outputs; no Python computation cross-checks them.
- **Money as `float`.** No `Decimal` usage anywhere in the codebase.
- **Unquantified-inclusion detection is prompt-trusted.** No deterministic check (e.g. regex for "included" without a quantity) backstops the LLM scan.

## Proposed evaluation harness

*This section is a design proposal — none of it exists in the repository.*

**Golden dataset shape.** Directory of cases, each: two input PDFs (or pre-extracted text to decouple from pypdf), two saved design-page snapshots, and an `expected.json` holding the target `ExtractResult`, the required `AmbiguityFlag` set (by item name + confidence), and bounds for the summary's numeric fields. Seed case #1 is the downlights scenario already encoded in `demo_data.py`; add a no-ambiguity case, an image-only PDF case, and an unparseable-response replay.

**Suite structure.**
1. *Unit (no network):* `_parse_json` fence/garbage handling, `get_provider` resolution order, `fetch_url` scheme rejection, truncation caps, schema round-trips, `detect_brand`.
2. *Contract (recorded LLM responses):* validated replay of extract/scan/summary responses through the Pydantic gates; malformed replays must fall back, and — once loud failures land — must surface.
3. *Behavioural (live model, nightly):* run golden PDFs through each provider; assert the downlights flag is raised with LOW confidence, no dollar figure appears without a source ref, and the summary carries the INTERNAL label.
4. *E2E (Streamlit AppTest):* wizard → processing → review → summary in demo mode, asserting the review page blocks the summary until all flags resolve.

**Gates and metrics.** CI blocks merge on units + contract. Behavioural tracks: ambiguity recall on golden flags (target 1.0 on the downlights class — this is the product's north-star failure mode), false-flag rate, schema-validation pass rate per provider, and numeric-consistency rate (model subtotals vs Python-recomputed subtotals) — the last becomes obsolete once reconciliation moves into Python per ARCHITECTURE.md.
