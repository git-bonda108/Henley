# Quote Comparison Agent — Streamlit app

Streamlit implementation of the competitor quote comparison agent: it compares a competitor builder's quote against the equivalent quote from a residential construction company, with human-in-the-loop ambiguity resolution before any comparison is finalised.

Full documentation lives at the repository root: [README](../README.md) · [Architecture](../docs/ARCHITECTURE.md) · [Evaluation](../docs/EVALUATION.md) · [Hardening](../docs/HARDENING.md).

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add API keys, or leave blank for demo mode
streamlit run streamlit_app.py
```

Open http://localhost:8501. The sidebar footer shows the active provider.

## Environment

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Primary reasoning provider |
| `ANTHROPIC_MODEL` | Code default `claude-sonnet-4-6` |
| `OPENAI_API_KEY` | Fallback provider + Agents SDK orchestration mode |
| `OPENAI_MODEL` | Default `gpt-4o` |
| `LLM_PROVIDER` | `anthropic` · `openai` · `demo` (unset: resolved by key presence) |
| `TAVILY_API_KEY` | Optional URL extraction; blank uses direct fetch |

**Demo mode:** set `LLM_PROVIDER=demo` or leave all keys blank — the app runs on fixtures, including the canonical downlights-ambiguity case, with no API calls.

## Flow

```
Extract → Ambiguity scan → [Human review] → Summary
```

- **Primary path:** sequential structured-JSON LLM calls (Anthropic), validated by Pydantic at every step.
- **Fallback:** OpenAI via direct API.
- **Agents SDK mode:** when `LLM_PROVIDER=openai`, a manager agent orchestrates the extract / scan / summarize steps exposed as function tools.

Design principle: the agent proposes; a human disposes. Never fabricate a number.

## Pages

1. **Home** — landing and principle cards
2. **New Comparison** — 4-section wizard (two quote PDFs, two design URLs, run context)
3. **Processing** — pipeline timeline and run log
4. **Review** — ambiguity confirmation cards (pauses the pipeline)
5. **Summary** — 9-section internal report with PDF / DOCX / Markdown export
