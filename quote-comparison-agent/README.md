# Quote Comparison Agent — Henley Homes / Fusion5

Streamlit demo of the **Competitor Quote Comparison Agent**: compares competitor builder quotes against Henley equivalents with human-in-the-loop ambiguity resolution.

## Quick start

```bash
cd quote-comparison-agent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your API keys
streamlit run streamlit_app.py
```

Open http://localhost:8501

## Environment

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Primary reasoning (recommended) |
| `ANTHROPIC_MODEL` | Default `claude-sonnet-4-20250514` |
| `OPENAI_API_KEY` | Fallback + OpenAI Agents SDK orchestration |
| `OPENAI_MODEL` | Default `gpt-4o` |
| `LLM_PROVIDER` | `anthropic` · `openai` · `demo` |
| `TAVILY_API_KEY` | Optional URL extraction |
| `GIT_TOKEN` | Placeholder for future git push / CI |

**Demo mode:** Set `LLM_PROVIDER=demo` or leave all API keys blank — uses rich fixtures including the canonical **downlights ambiguity** case.

## Agent architecture

```
Extract → Ambiguity scan → [Human review] → Summary
```

- **Primary:** Anthropic Claude (structured JSON modes per FRD)
- **Fallback:** OpenAI via direct API
- **OpenAI Agents SDK:** When `LLM_PROVIDER=openai`, a manager agent orchestrates extract / scan / summarize tools

Design principles (SDD §2.5): the agent proposes; a human disposes. Never fabricate a number.

## Pages

1. **Home** — Fusion5 hero, principle cards
2. **New Comparison** — 4-step wizard (PDFs, URLs, radio groups)
3. **Processing** — Agent timeline + live log
4. **Review** — Ambiguity confirmation cards (downlights case)
5. **Summary** — 9 collapsible sections, export PDF/DOCX/Markdown

## Brand

Fusion5 "Go Beyond" palette: grape `#2A1A3D`, orange `#FF6B1A`, cream `#FFF8F2`, Inter + JetBrains Mono.
