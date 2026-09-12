# Hardening

## Current posture (as built)

This is a demonstration build. Its security properties are those of a local Streamlit app:

- **Authentication / authorization:** none. Anyone who can reach port 8501 can upload documents, trigger LLM calls on the operator's API keys, and download summaries. There are no users, roles, or audit identities — the "sales rep" field is free text.
- **Secrets handling:** API keys load from a local `.env` via `python-dotenv`; `.env` and `.streamlit/secrets.toml` are gitignored at both repo and app level, and `.env.example` ships empty values. A scan at HEAD found **no committed credentials**. Keys are read from `os.environ` at call time and never logged or rendered; the sidebar exposes only the provider name.
- **Input handling:** PDFs are size-capped in UI copy (≤25 MB) but not enforced in code; bytes are parsed in-process by `pypdf`. URL fetching validates the scheme only — the app will fetch any user-supplied `http(s)` URL (an SSRF surface if hosted inside a private network) and follows redirects. All extracted text is character-capped before reaching the model.
- **Output handling:** several components render f-strings with `unsafe_allow_html=True` (`brand.py`, review/summary pages). Values interpolated there include LLM- and user-derived strings, so a hostile quote document could inject markup into the operator's own view. Low stakes single-user; must be closed before multi-user hosting.
- **Error handling:** provider or parse failures degrade silently to demo fixtures; the Agents SDK path swallows exceptions wholesale (`except Exception: pass`). Nothing distinguishes "real result" from "fixture fallback" in the UI beyond the sidebar provider label.
- **Observability:** none beyond the in-session log list. No structured logging, no request ids in logs, no token/cost accounting, no tracing of LLM calls.
- **Data at rest / retention:** nothing persists — session state is in-memory, per-Streamlit-session, with a fresh session id per comparison and no cross-session sharing. The declared `SESSION_TTL_MINUTES` is not implemented, but since nothing is written to disk there is nothing for a sweep to clean.
- **Network egress:** Anthropic, OpenAI, Tavily APIs, plus arbitrary user-supplied design URLs. Quote text (commercially sensitive pricing) is sent to whichever LLM provider is active.

## Ladder to production

### Stage 1 — Identity and keys
- Put the app behind SSO (reverse proxy with OIDC, or Streamlit's auth integrations); derive the sales-rep identity from the login rather than free text.
- Move provider keys out of `.env` into a secrets manager; inject at deploy time. Scope one key per environment and rotate on a schedule.
- Enforce the 25 MB upload cap and page-count limits in code, not copy; reject encrypted/malformed PDFs explicitly.
- Constrain `fetch_url` with an allowlist of builder-website domains (the wizard already defaults to two known domains), block private-address ranges, and cap redirect chains.
- Replace `unsafe_allow_html` interpolations of untrusted strings with escaped rendering.

### Stage 2 — Monitoring and failure honesty
- Make fallbacks loud: tag every result with its provenance (provider, model id, or `fixture`) in the UI and exports; alert when production traffic serves fixtures.
- Replace `except Exception: pass` with logged, surfaced errors carrying the session id.
- Structured logs per pipeline step (session id, step, latency, token counts, validation outcome); ship to a log store. Add cost metering per comparison.
- Land the evaluation harness (EVALUATION.md) in CI, gating deploys on units + contract tests and tracking ambiguity recall nightly.

### Stage 3 — Deployment
- Containerise; run Streamlit behind TLS on a private network segment; pin dependencies with hashes and scan the image.
- Externalise session state (e.g. Redis with TTL) if moving beyond single-instance, implementing the declared-but-unbuilt TTL semantics at the same time.
- Rate-limit comparisons per user to bound LLM spend; set per-request budget ceilings.
- Move deterministic arithmetic into Python (`Decimal`) per ARCHITECTURE.md so the deployed system's dollar figures are auditable computations, not model output.

### Stage 4 — Compliance and data governance
- Classify quote PDFs as commercially sensitive: document the LLM data path, use provider endpoints with no-training/zero-retention terms, and record that decision.
- Retention policy for exports (the only artefacts that leave the app) — watermarked, access-logged, and expiring if stored server-side.
- Audit trail: persist per-session ledgers (who ran what, which flags were resolved how, which model produced each section) — the `AmbiguityResolution` records and session ids are the natural spine for this.
- Periodic red-team of the anti-fabrication rules with adversarial quote documents (prompt injection via PDF text is untested today).

## Secrets removed from HEAD — rotate these credentials and purge history

None. No credentials, tokens, private keys, or populated `.env` files were found at HEAD; `.env.example` contains placeholders only.
