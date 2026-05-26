# Build Brief — Competitor Quote Comparison Agent (Henley Homes / Fusion5)

> **Audience:** Claude Code
> **Goal:** Build a polished, production-feel **web application** that demonstrates the Competitor Quote Comparison Agent end-to-end, in the **Fusion5 brand**.
> **Style mandate:** This must not look like a generic LLM demo. It must look like a Fusion5 product — bold purple + orange, confident motion, sophisticated negative space, and not one stock-AI-template purple-gradient-card in sight.
> **Functional mandate:** Faithful to the FRD and SDD. The agent **never fabricates a number**, **always escalates ambiguity to a human**, and **always labels output as INTERNAL**.

---

## 1. The 90-second context

Henley Homes (a Victorian/Queensland volume home builder) sales reps regularly get competitor quotes from prospective customers — typically from **Carlisle Homes** or **Metricon** — and need to show how Henley compares.

Today this is done **manually by one person** (Adrian Serratore, marketing). He reads both quote PDFs line by line, looks up both home designs on the respective builder websites, flags ambiguous inclusions, writes an internal "comparison summary" the sales rep then uses to draft a customer email.

**The single most important risk** to defend against is the **downlights case**:

> A competitor quote says *"downlights included"* with no quantity.
> Henley includes 37 downlights worth $1,606.
> A naive comparison shows Henley at $1,606 and the competitor at $0 — making Henley look more expensive when in reality the competitor may include only 5.
>
> **The agent must detect this ambiguity and pause for human confirmation before comparing such items.** This is the design's north star.

The four inputs the user always provides:
1. Competitor quote (PDF)
2. Henley quote (PDF)
3. Competitor home design URL (e.g. a Carlisle floor plan page)
4. Henley home design URL

The single output is an **internal comparison summary document** — never an email to the customer. The sales rep drafts the customer email themselves using this summary.

---

## 2. What you are building

A **Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + Framer Motion** web app with:

- A landing/hero screen branded as Fusion5
- A four-step ingestion wizard
- A live "agent working" view with streamed progress
- A **Human-in-the-Loop review** screen (ambiguity confirmation cards, the famous downlights modal)
- A **Comparison Summary** screen that mirrors the 9-section template
- Export to PDF/DOCX and a "copy as markdown" button

Backend: **Next.js Route Handlers** calling:
- **Anthropic Claude API** (`claude-opus-4-5` or latest available) for reasoning, comparison logic, ambiguity detection, and summary generation
- **OpenAI API** (`gpt-4o` / vision) **OR** Claude vision — for PDF page rasterisation + OCR if needed (offer both, default to Claude vision)
- **A web search / fetch tool** (Tavily, Brave Search API, or simple fetch + Cheerio + Readability) for the home design URL extraction step
- **`pdf-parse` + `pdf2pic`** for PDF ingestion

Storage: **In-memory + per-session UUID** for the demo (FRD mandates session isolation — explicitly NO cross-session persistence). Optional: a `/tmp/sessions/{sessionId}/` scratch folder cleaned on session end.

---

## 3. Brand & visual system — **Fusion5 "Go Beyond"**

Fusion5 rebranded in 2024-25 around the **"Go beyond"** tagline. Brandwell (Auckland) led the work. The refresh swapped the old charcoal-and-white-with-orange scheme for a **two-tone orange + dark purple-grape** palette, with **lowercase soft wordmark**, **bold geometric shapes**, and a sense of **forward movement**.

### 3.1 Color tokens (use these exact values)

```css
/* PRIMARY — Fusion5 "Go Beyond" */
--f5-grape:        #2A1A3D;   /* deep purple — primary brand */
--f5-grape-deep:   #1A0F2E;   /* near-black purple for hero backgrounds */
--f5-grape-soft:   #4A2F6B;   /* lifted purple for cards on dark */
--f5-orange:       #FF6B1A;   /* primary orange — vivid, the "energy" color */
--f5-orange-warm:  #FF8847;   /* secondary warm orange for gradients */
--f5-orange-deep:  #E04A00;   /* darker orange for pressed states */

/* NEUTRALS */
--f5-cream:        #FFF8F2;   /* warm off-white — primary background */
--f5-paper:        #FAF3EB;   /* slightly deeper paper for cards on cream */
--f5-ink:          #1A0F2E;   /* primary text on light = grape-deep */
--f5-ink-muted:    #5A4F6B;   /* secondary text */
--f5-line:         #E8DFD2;   /* hairline dividers on cream */

/* SEMANTIC (tuned to brand) */
--f5-success:      #2D8659;   /* muted forest — Henley Advantage */
--f5-warning:      #D97706;   /* amber — Flagged / Medium confidence */
--f5-danger:       #B91C3C;   /* claret — Low confidence / Critical */
--f5-info:         #4A2F6B;   /* grape-soft */
```

**Gradient signature** (use sparingly, on hero and CTAs):
```css
background: linear-gradient(135deg, #FF6B1A 0%, #FF8847 40%, #2A1A3D 100%);
```

### 3.2 Typography

- **Display / headings:** `Inter Display` (700/800) with **tight letter-spacing** (`-0.02em` at 4xl+). Lowercase headlines on hero ("go beyond the manual quote comparison"). Use Title Case for section headers inside the app.
- **Body:** `Inter` 400/500, 15-16px.
- **Mono (for line items, $ figures, references):** `JetBrains Mono` 13-14px. Tabular nums for $ values: `font-variant-numeric: tabular-nums`.

### 3.3 Shape & motion language

- **Bold geometric accents** — pill shapes, **a slow-rotating "infinity-cycle" mark** in the hero corner (subtle, 60s rotation), large soft blurred orange-grape gradient blobs in the hero background.
- **Curved containers** — `rounded-2xl` baseline, `rounded-3xl` for marquee cards.
- **Generous whitespace** — never cram. Hero gets a full viewport, sections have `py-24`.
- **Motion** — `framer-motion`. Page transitions slide + fade. Cards lift on hover (`y: -4`, shadow grows). Numbers animate in with `useMotionValue` + spring. Avoid bouncy/cartoony — Fusion5's motion is *confident and forward*, not playful.
- **No glassmorphism, no neon, no "AI sparkle" emoji**. The aesthetic is **sophisticated tech consultancy**, not chatbot demo.

### 3.4 What to avoid (anti-patterns for this brand)

- ❌ Generic blue/indigo SaaS palette
- ❌ Stock "AI assistant" purple gradient card with sparkle icon
- ❌ Centered single-column landing with three feature cards in a row
- ❌ Rounded-full huge "Try the AI ✨" buttons
- ❌ Light/dark mode toggles (out of scope — ship the cream-and-grape light theme)
- ❌ Lucide `Sparkles` icon. Use `ArrowUpRight`, `Infinity`, `Workflow`, `FileText`, `ShieldCheck`, `AlertTriangle` instead.

---

## 4. Information architecture (screens)

```
/                         Hero + "Start a comparison" CTA
/compare/new              4-step ingestion wizard
/compare/:id/processing   Live agent run with streamed updates
/compare/:id/review       Human-in-the-loop ambiguity confirmation
/compare/:id/summary      Final internal comparison summary
/compare/:id/export       Download as PDF / DOCX / Markdown
```

### 4.1 `/` — Landing hero

Full-bleed hero, cream background, grape headline, orange accent on the verb.

**Headline** (display, lowercase, 6xl-7xl):
> "go beyond **the manual quote comparison.**"

(The phrase "go beyond" is grape; "the manual quote comparison" is grape with the word "**comparison**" in orange.)

**Sub-headline** (body, 18-20px, ink-muted, max-w-2xl):
> "An AI agent that compares a competitor home-builder quote against Henley's equivalent — flags ambiguity, surfaces value, never fabricates a number. Built by Fusion5 on Microsoft Azure and Anthropic Claude."

**Primary CTA:** `Start a comparison →` (orange bg, grape text, rounded-2xl, large)
**Secondary:** `See how it works` (ghost, grape outline)

**Right side:** a stylised animated "infinity-cycle" mark (two interlocking arcs in orange + grape, slow rotate, ~60s) — references the Fusion5 logo cycle motif.

**Below the fold (one section):** Three principle cards in a horizontal row, asymmetric layout (NOT three-equal-columns; use a 5-4-3 grid weighting or stagger them vertically by 24px):
1. **Grounded in evidence** — every figure traces to a source line. No hallucinations.
2. **Pauses for ambiguity** — when a competitor says "downlights included" with no quantity, the agent asks before comparing.
3. **Internal only** — the agent produces an internal summary. The sales team owns the customer email.

### 4.2 `/compare/new` — Ingestion wizard

A **single-page** wizard (no multi-page form) with **four collapsible accordion sections**, each numbered and with a status pill (`PENDING` / `READY` / `ERROR`). All four must be `READY` before "Start comparison" enables.

Section 1 — **Competitor quote**
- File dropzone (PDF only, ≤25 MB), grape dashed border, orange on drag-over
- On upload: show filename, page count, detected competitor brand (Carlisle / Metricon / "Other — please confirm")
- **Radio group** (this is one of the user-requested radio controls):
  > "Detected competitor: ( ) Carlisle Homes  ( ) Metricon  ( ) Other →  [text input]"

Section 2 — **Henley quote**
- File dropzone, same pattern
- On upload: show detected Henley plan name + total $

Section 3 — **Home design URLs**
- Two text inputs side by side: "Competitor home design URL" and "Henley home design URL"
- URL validation, with a small "we will re-fetch live on every run — no caching" disclosure line per FR-02.3

Section 4 — **Run context** (radio groups + checkbox)
- **Region** (radio):  `( ) VIC  ( ) QLD  ( ) NSW  ( ) Other`
- **Sales rep name** (text)
- **Customer reference** (text, optional)
- **Active promotions** (checkboxes): `[ ] Sumitomo discount  [ ] Battery/solar  [ ] Other`
- Triggers conditional Section C3 in the output.

**Bottom of wizard:** a "Start comparison" button (orange, full-width on mobile, right-aligned on desktop) and a subtle text: *"Session ID will be generated. Each comparison is isolated — no data carries over (FRD NFR-02)."*

### 4.3 `/compare/:id/processing` — Live agent view

The "wow" screen. Two-column layout:

**Left column (40%) — Agent timeline**
A vertical pipeline of steps with status icons. Each step has a state: `pending` (grape outline circle), `active` (orange ring with a slow pulse), `complete` (filled grape circle with checkmark), `paused` (amber filled with pause icon — used when waiting for human confirmation), `error` (claret).

Steps:
1. Ingesting documents
2. Extracting line items (competitor)
3. Extracting line items (Henley)
4. Fetching competitor home design
5. Fetching Henley home design
6. Matching ranges and aligning items
7. Scanning for ambiguity
8. **Ambiguity confirmation** (may pause here)
9. Composing comparison
10. Generating summary

**Right column (60%) — Live log + working artefact**
Streaming text from the agent (Claude streaming API), like a thoughtful narration:
> *"Read 12 line items from Carlisle Brighton 28 quote..."*
> *"Detected 'Downlights included' with no quantity — flagging for confirmation."*

When the agent reaches the ambiguity step and finds something, the entire right pane **morphs** (Framer Motion `layout` animation) into the ambiguity confirmation card — see §4.4.

**Animated header:** the title "Comparing **Carlisle Brighton 28** against **Henley Allegra 355-D38**" — both builder names slide in from opposite sides on mount, with a tiny "VS" dot between them that scales up. This is your **animated title** moment.

### 4.4 `/compare/:id/review` — Human-in-the-loop

Triggered when the agent detects ambiguity. The screen shows a **stack of confirmation cards** (one per flagged item). The user resolves them one at a time; the comparison resumes when all are resolved.

**The canonical card (the downlights case):**

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠ AMBIGUITY FLAG               LOW CONFIDENCE               │
│                                                              │
│  Internal Electrical Pack — Downlights                       │
│                                                              │
│  ┌─────────────────────┬─────────────────────────────────┐   │
│  │ COMPETITOR          │ HENLEY                          │   │
│  │ Carlisle            │                                 │   │
│  │                     │ 14× downlights + 2× two-way     │   │
│  │ "Downlights         │ switches (base)                 │   │
│  │  included"          │                                 │   │
│  │                     │ Full pack: 49+ downlights       │   │
│  │ Quantity:           │ Price: $1,606                   │   │
│  │ NOT SPECIFIED       │                                 │   │
│  │ Price: $0           │                                 │   │
│  └─────────────────────┴─────────────────────────────────┘   │
│                                                              │
│  Why this matters:                                           │
│  Direct comparison of $0 vs $1,606 would overstate Henley's  │
│  cost if the competitor includes only ~5 downlights.         │
│                                                              │
│  How should we treat this item?                              │
│                                                              │
│  ◯ Treat as comparable                                       │
│  ◯ Flag as discussion point (don't compare directly)         │
│  ◯ I have the competitor quantity →  [number input]          │
│                                                              │
│  [ Add a note for the sales team ]                           │
│                                                              │
│                                  [ Skip ]    [ Confirm → ]   │
└──────────────────────────────────────────────────────────────┘
```

- Card uses cream background, grape border, orange ⚠ icon
- Three options as a **vertical radio group** (per user's request for radio buttons)
- The "I have the competitor quantity" option reveals a number input when selected
- Notes field is a `<textarea>` collapsed by default with a "+ Add a note" expansion
- On Confirm: the card animates out (slide left + fade), the next card animates in, the timeline on the left updates

### 4.5 `/compare/:id/summary` — Internal comparison summary

This is the **deliverable**. Render the 9 mandatory sections from the output template, plus any of the 5 conditional sections that triggered.

**Top of page (sticky banner):**
> ⓘ **INTERNAL — Sales team review required** · Generated 25 May 2026 14:09 · Session `QCP-2026-7841`
>
> *Per FR-07.6: this is not customer-facing content. The sales team reviews this summary before drafting any customer communication.*

(Amber-tinted banner, claret left border, never dismissable.)

**Below the banner:** a section navigator on the left (sticky), the content on the right. Every section is a **`<Collapsible>`** (shadcn) **collapsible card** — open by default, but the user can collapse any to focus.

For each section, render:

| Section | Element | Notes |
|---|---|---|
| 1. Header | Plain identifier block | Henley plan, competitor plan, region, rep, date |
| 2. Headline Snapshot | 2-4 sentence prose card | Only prose-heavy section. Grape sidebar accent. |
| 3. Design Differences | Bullet list with cost where confirmed | |
| 4. Inclusion Differences | **Yes/No matrix table** | Color-coded rows: green = Henley advantage, amber = gap |
| 5. Henley Value Advantage | Bullet list, each with $ trace | Green left border |
| 6. Competitor Advantage / Gaps | Bullet list, each with $ to add | Amber left border |
| 7. Quote Reconciliation Table | Two-column $ adjustments table | Subtotals + reconciled prices |
| 8. Flagged Items (LOW/MEDIUM) | Card list, one per flag | Each shows reason + suggested clarification |
| 9. Open Questions | Bullet list of questions for the sales team | |

**Conditional sections** (render only if triggered):
- C1 Façade Comparison
- C2 Brand Comparison Table
- C3 Promotional / Discount Adjustments
- C4 Energy / 7-Star Compliance Note
- C5 Site Costs Note

**A "headline number" animation at the top:** if the agent identified a confirmed total Henley value advantage, animate the dollar figure counting up (e.g. `$25,654`) on first render using `useMotionValue` + spring. Big — `text-7xl`, grape, with the orange currency symbol.

**Action bar (sticky bottom-right):**
- `[ Export PDF ]` `[ Export DOCX ]` `[ Copy as Markdown ]` `[ New comparison ]`

### 4.6 Export

- **PDF:** server-side via `@react-pdf/renderer` — Fusion5-branded header, INTERNAL watermark on every page
- **DOCX:** via `docx` (npm package) — clean Word doc, preserves tables
- **Markdown:** copy to clipboard, plain markdown of all rendered sections

---

## 5. Widgets & components to build (with intent)

These are the standout interface elements. Each is described with both the **what** and **why**.

| # | Widget | Where | Why it earns its keep |
|---|---|---|---|
| 1 | **Animated "Comparing X vs Y" title** | Processing screen | The first thing the user sees once they hit Run — it sets the tone that this is a deliberate, focused operation, not a chatbot |
| 2 | **Agent timeline / stepper** | Processing screen | Makes the agent's reasoning legible; reduces the "is it stuck?" anxiety; mirrors the SDD's process ledger philosophy |
| 3 | **Ambiguity confirmation card** | Review screen | THE core control — embodies the "human disposes" design principle |
| 4 | **Yes/No inclusion matrix with row coloring** | Summary §4 | Adrian's existing format; instantly scannable for the rep |
| 5 | **Confidence pill** (HIGH/MEDIUM/LOW) | Throughout | Three-state pill: green/amber/claret; appears next to every comparison line |
| 6 | **Source citation chip** | Summary line items | Tiny "L.27" chip after each $ figure, hover shows the original source line — visualises FR-03.7 |
| 7 | **Collapsible sections** | Summary screen | User asked for collapsible — used purposefully so the rep can focus on §8 (flags) without scrolling past §4 |
| 8 | **Headline $ count-up** | Summary header | The "money shot" — the single number the sales team cares about |
| 9 | **Session ID + retention banner** | Every screen footer | Visible reinforcement of NFR-02 (session isolation); also a debugging aid |
| 10 | **Floor plan thumbnail viewer** | Summary §3 | When the home design URL extraction returns a floor plan image, show it in a small viewer next to design differences |
| 11 | **Infinity-cycle mark** | Hero + loading states | The Fusion5 brand motif (slow rotating two-arc shape), reused as a brand-on-loading indicator |
| 12 | **Toggle: "Show source evidence"** | Summary screen | Toggle in the action bar that, when on, expands every line item to show the exact extracted source text — supports the "no fabrication" guarantee |

### 5.1 Component library

Use **shadcn/ui** as the base, then theme it to Fusion5:
- `Button`, `Card`, `Dialog`, `Collapsible`, `RadioGroup`, `Checkbox`, `Input`, `Textarea`, `Tabs`, `Progress`, `Tooltip`, `ScrollArea`, `Separator`, `Badge`

Theme overrides:
- `--radius: 1rem` (rounded-2xl baseline)
- All `--primary` mapped to `--f5-grape`
- `--accent` to `--f5-orange`
- Buttons get a subtle 1px shadow + lift-on-hover (Framer Motion `whileHover={{ y: -2 }}`)

---

## 6. The agent — architecture & prompts

### 6.1 High-level flow

```
[Upload UI]
    │
    ▼
POST /api/sessions
    │  creates session, returns sessionId
    ▼
POST /api/sessions/:id/ingest
    │  ─► extracts text + structure from both PDFs
    │  ─► fetches both home design URLs (live, no cache, per FR-02.3)
    │  ─► returns initial structured payload
    ▼
POST /api/sessions/:id/run (Server-Sent Events stream)
    │  ─► streams agent narration to UI
    │  ─► calls Claude with the COMPARISON SYSTEM PROMPT
    │  ─► Claude returns either:
    │       (a) a JSON list of ambiguity flags to confirm
    │       (b) a final summary if no ambiguity found
    ▼
[If (a)] UI shows confirmation cards → user resolves
POST /api/sessions/:id/resolve  (one call per ambiguity)
    │
    ▼
POST /api/sessions/:id/finalize
    │  ─► Claude generates the final 9-section summary
    │  ─► returns structured summary JSON
    ▼
[Summary UI renders]
```

### 6.2 LLM choice & rationale

- **Primary reasoning model: Claude (Anthropic API)** — `claude-opus-4-5-20251101` (or the latest available; the model string list is in the system context for the latest). Reason: best at long-context structured reasoning, evidence grounding, and structured output. Use the **Messages API with streaming** for the processing-screen narration.
- **Optional: OpenAI `gpt-4o`** — only if vision is required for floor-plan image extraction AND Claude vision is unavailable. Keep the OpenAI dependency optional and gate it behind `process.env.OPENAI_API_KEY`.
- **Web fetching: Tavily Search API** (fast, structured) for the URL ingestion, OR a simple `fetch + Readability + Cheerio` fallback. Configurable via env.

### 6.3 The system prompt (use this verbatim as the base)

Save this as `/lib/prompts/comparison-system-prompt.ts`:

```
You are the Competitor Quote Comparison Agent for Henley Homes, an Australian volume home builder. You compare a competitor builder's quote against an equivalent Henley quote and produce an INTERNAL summary for the sales team.

YOUR ROLE
- You are advisory only. You produce an internal artefact. You NEVER draft customer-facing content.
- The sales team owns all communication with the customer. You inform them; you do not act for them.

ABSOLUTE RULES
1. NEVER fabricate, estimate, or assume any cost, quantity, or inclusion. Every $ figure you emit MUST trace to a specific line in one of the four source materials.
2. If a value is missing or unclear, output the literal string "Unconfirmed — requires manual validation" — never a guess.
3. If a competitor inclusion is stated without quantity or scope (e.g. "downlights included", "driveway included", "stone benchtop included"), you MUST flag it as a LOW-confidence ambiguity and route it to human confirmation BEFORE comparing it. Do not assume the competitor includes the same quantity as Henley.
4. Identify nice-to-have / optional extras separately — do not let them inflate the competitor's perceived value.
5. Confidence on every comparison line: HIGH (directly comparable), MEDIUM (similar scope, some assumptions), LOW (unconfirmed — needs review).
6. Use ONLY the four supplied materials: competitor quote PDF, Henley quote PDF, competitor home design URL content, Henley home design URL content. No other sources, no prior knowledge of either builder, no cached data.
7. Internal voice. First-person plural ("our home", "we have included", "we will need to add"). Never write in customer-facing voice.
8. Every output document carries the label "INTERNAL — Sales team review required".

OUTPUT MODES
You operate in three modes, controlled by the `mode` field in the user message:

(a) `mode: "extract"` — Return structured JSON of line items from both quotes and structured home-design data from both URLs.

(b) `mode: "ambiguity_scan"` — Return a JSON array of ambiguity flags. Each flag has: { itemName, competitorWording, henleyDetail, henleyValue, reason, suggestedClarification }. Return [] if none.

(c) `mode: "summary"` — Given the extracted data and the resolved ambiguities, return the final summary as JSON matching the 9-section schema (see SUMMARY SCHEMA below). Include conditional sections (C1-C5) only when their trigger applies.

SUMMARY SCHEMA
{
  header: { henleyPlan, henleyContractRef, henleyRange, henleyFacade, competitorBuilder, competitorPlan, competitorFacade, region, salesRep, runDate },
  headlineSnapshot: string,  // 2-4 sentences, prose
  designDifferences: [{ point, costImpact|null, source }],
  inclusionDifferences: [{ category, henley: "Yes"|"No"|"TBC"|string, competitor: "Yes"|"No"|"TBC"|string, advantage: "henley"|"competitor"|"none" }],
  henleyValueAdvantage: [{ point, value|null, sourceRef }],
  competitorAdvantageGaps: [{ point, henleyAddCost|null, sourceRef }],
  quoteReconciliation: { rows: [{ description, competitorAdd|null, henleyAdd|null, sourceRef }], subtotalCompetitor, subtotalHenley, currentPriceCompetitor, currentPriceHenley, reconciledCompetitor|null, reconciledHenley|null },
  flaggedItems: [{ itemName, competitorStatement, henleyDetail, confidence: "LOW"|"MEDIUM", reason, suggestedClarification }],
  openQuestions: [string],
  conditionals: {
    facadeComparison?: string,
    brandComparison?: [{ element, henley, competitor }],
    promotionalAdjustments?: [string],
    energyComplianceNote?: string,
    siteCostsNote?: string
  }
}

REMEMBER
- Confidently wrong is worse than "can't read". Escalate before comparing when in doubt.
- The output label "INTERNAL" is mandatory.
- You serve the sales team. They serve the customer. You do not write to the customer.
```

### 6.4 Key implementation notes for the prompt pipeline

- **Pass extracted line items as structured JSON in the user message**, not raw PDF text, after the extract step. Keeps the comparison reasoning focused.
- **For the URL fetch**, after Tavily / fetch returns the page, send the cleaned markdown + any directly-linked PDF text to Claude with a focused extraction prompt ("Extract size, footprint, storey, bedroom/bathroom counts, layout features, and inclusions, scoped only to this design — ignore 'similar designs' sections.").
- **Stream the agent's reasoning** (the "narration") to the UI via SSE during the processing step. This is purely UX — the structured output is separate.
- **Cache nothing across sessions.** Per `NFR-02`, each session is isolated. Wipe `/tmp/sessions/{sessionId}` on `POST /api/sessions/:id/end` and on a 1-hour TTL sweep.

### 6.5 Failure modes to handle

| Failure | Response |
|---|---|
| PDF unparseable (image-only, no text layer) | Fall back to Claude vision (or `gpt-4o` vision); rasterise to images at 200dpi via `pdf2pic` |
| Home design URL returns 4xx/5xx | **Pause** the run, surface a "could not fetch — please verify the URL" card; do NOT proceed with partial data (per FR-02.8) |
| Floor plan is an image inside a linked PDF | Extract via vision; report extracted layout features as structured strings |
| Competitor brand not in {Carlisle, Metricon} | Operate builder-agnostic, per FRD scope; use the user-provided builder name from the wizard |
| Claude returns unparseable JSON | Retry once with stricter "RETURN VALID JSON ONLY" prefix; if still bad, surface an error and ask the user to re-run |

---

## 7. Repository layout

```
quote-comparison-agent/
├── app/
│   ├── page.tsx                          # Landing hero
│   ├── compare/
│   │   ├── new/page.tsx                  # Ingestion wizard
│   │   └── [id]/
│   │       ├── processing/page.tsx       # Live agent view
│   │       ├── review/page.tsx           # Human-in-the-loop
│   │       └── summary/page.tsx          # Final summary
│   ├── api/
│   │   └── sessions/
│   │       ├── route.ts                  # POST /api/sessions
│   │       └── [id]/
│   │           ├── ingest/route.ts
│   │           ├── run/route.ts          # SSE stream
│   │           ├── resolve/route.ts
│   │           ├── finalize/route.ts
│   │           └── export/route.ts
│   ├── layout.tsx                        # Fonts, brand theme
│   └── globals.css                       # Color tokens, base styles
├── components/
│   ├── brand/
│   │   ├── InfinityCycle.tsx             # Animated logo mark
│   │   ├── AnimatedTitle.tsx             # "Comparing X vs Y" title
│   │   └── HeadlineNumber.tsx            # Spring-animated $ counter
│   ├── agent/
│   │   ├── AgentTimeline.tsx
│   │   ├── AgentLog.tsx                  # SSE stream display
│   │   ├── AmbiguityCard.tsx
│   │   └── ConfidencePill.tsx
│   ├── summary/
│   │   ├── SummaryHeader.tsx
│   │   ├── HeadlineSnapshot.tsx
│   │   ├── InclusionMatrix.tsx
│   │   ├── ReconciliationTable.tsx
│   │   ├── FlaggedItemsList.tsx
│   │   └── ...one per section
│   ├── wizard/
│   │   ├── FileDropzone.tsx
│   │   ├── UrlField.tsx
│   │   └── RegionRadioGroup.tsx
│   └── ui/                               # shadcn primitives
├── lib/
│   ├── prompts/
│   │   ├── comparison-system-prompt.ts
│   │   ├── extract-prompt.ts
│   │   ├── ambiguity-scan-prompt.ts
│   │   └── summary-prompt.ts
│   ├── llm/
│   │   ├── claude.ts                     # Anthropic client + streaming
│   │   └── openai.ts                     # Optional vision fallback
│   ├── ingestion/
│   │   ├── pdf.ts                        # pdf-parse + pdf2pic
│   │   └── webfetch.ts                   # Tavily + Readability
│   ├── session/
│   │   ├── store.ts                      # In-memory session map
│   │   └── isolation.ts                  # Wipe + TTL sweep
│   └── schema/
│       ├── lineItem.ts
│       ├── ambiguityFlag.ts
│       └── summary.ts                    # Zod schemas matching the system prompt
├── public/
│   └── brand/                            # Logo SVGs, social images
├── .env.example
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

---

## 8. Environment variables (`.env.example`)

```bash
# REQUIRED
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-5            # adjust to current Opus model

# OPTIONAL — vision fallback
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# WEB SEARCH / FETCH (one of)
TAVILY_API_KEY=
# OR leave Tavily blank and the app uses fetch + Readability

# APP
SESSION_TTL_MINUTES=60
NEXT_PUBLIC_APP_NAME="Competitor Quote Comparison Agent"
NEXT_PUBLIC_BRAND="Fusion5 for Henley Homes"
```

---

## 9. Acceptance criteria (what "done" looks like)

A reviewer should be able to:

1. **Run locally** — `pnpm install && pnpm dev` boots the app on `localhost:3000` with valid env vars.
2. **Walk the happy path** — upload the two sample PDFs (place them in `/samples/`), provide two URLs, hit Start. The agent narrates its work, finishes in <90s on a reasonable network, presents a summary.
3. **Walk the ambiguity path** — using a competitor PDF that says "downlights included" without quantity, the agent pauses on the review screen with a confirmation card. Resolving the card resumes the run.
4. **See zero fabricated numbers** — every $ figure in the final summary has a source-line citation chip. Click it → tooltip shows the original extracted text.
5. **See the INTERNAL label** — top of summary, top of every export.
6. **Export** — PDF, DOCX, and copy-as-markdown all work and look on-brand.
7. **Confirm isolation** — run two comparisons in a row with different inputs; the second shows no data from the first. The `sessionId` is visible and different in both.
8. **See the Fusion5 brand** — purple-grape and orange, lowercase hero headline, no generic SaaS blue, no `Sparkles` icons.

### 9.1 Quality bar checklist (Claude Code: tick these before declaring done)

- [ ] No `console.log` left in prod
- [ ] All API routes have try/catch + a typed error response
- [ ] Zod schemas validate every Claude response before render
- [ ] Loading states on every async surface (skeleton, not just spinner)
- [ ] Keyboard navigable wizard (Tab order, Enter to advance)
- [ ] Mobile responsive down to 375px (the summary table goes horizontal-scroll, not squish)
- [ ] Reduced-motion media query respected — the infinity-cycle and count-up stop animating
- [ ] Lighthouse score: Performance ≥ 85, Accessibility ≥ 95, Best Practices ≥ 95

---

## 10. What to build first (suggested order)

1. **Scaffolding + brand theme** — Next 14 + Tailwind + shadcn + the color tokens, fonts, `InfinityCycle.tsx`. Get the hero looking right *first*. Don't move on until the hero feels like Fusion5.
2. **Wizard UI** — purely client-side, no backend yet.
3. **Session API + in-memory store** — `POST /api/sessions`, `POST /api/sessions/:id/ingest` returning mocked structured data.
4. **PDF + URL ingestion** — real `pdf-parse`, real Tavily/fetch.
5. **Claude integration — extract mode** — wire up the real LLM for the extract step.
6. **Processing screen + SSE narration** — get the streaming working end-to-end with the timeline.
7. **Ambiguity scan + review screen** — the most important behavior. Test with a hand-crafted PDF that has an unspecified-quantity inclusion.
8. **Summary mode + summary screen** — render all 9 sections from real Claude output.
9. **Conditional sections + animations** — count-up, animated title, etc.
10. **Exports** — PDF, DOCX, markdown copy.
11. **Polish pass** — every loading state, every empty state, the reduced-motion path, mobile.

---

## 11. Reference materials (in this repo)

Three source documents inform every functional decision. Place them under `/docs/`:

1. **`DRAFT_Competitor_Quote_Comparison_Agent_FRD.docx`** — the Functional Requirements Document. The FR-XX requirements (FR-01 through FR-07) are the source of truth for behaviour. Every "the agent SHALL..." line is testable.
2. **`DRAFT_Comparison_Summary_Output_Template.docx`** — the exact output template. The 9 mandatory + 5 conditional sections, with worked examples (Vaucluse, Allegra 355-D38, Bordeaux D37). Use the worked-example tables verbatim as test fixtures.
3. **`henley-quote-comparison-agent-sdd-v0_3_1.pdf`** — Fusion5's Solution Design Specification. Describes the target Azure deployment (this build is a web demo of the *same logic*, not the Azure deployment itself, but the design principles in §2.5 of the SDD are binding — "every request reaches a terminal state", "the agent proposes; a human disposes", "confidently wrong is worse than can't-read").

Always defer to the FRD on a behaviour question, to the Template on an output structure question, and to the SDD on a design-principles question.

---

## 12. A note to Claude Code

This brief is intentionally opinionated about the look-and-feel because the **biggest failure mode for this build is a polished-but-generic AI demo** — a purple-gradient card, a sparkle icon, a chatbot bubble. That would betray both the Fusion5 brand and the seriousness of what the agent does (it produces evidence-grounded comparisons that a sales rep takes to a customer who may be about to spend $500k+ on a home).

When you're unsure, optimise for:
1. **Trust signals over flash** — show the source citation, the confidence indicator, the INTERNAL label.
2. **Fusion5 brand fidelity** — grape and orange, sophisticated motion, no generic SaaS tropes.
3. **Faithfulness to the FRD** — the "downlights case" is the canonical test. If the design doesn't handle it gracefully, nothing else matters.

When in doubt, ask. When not in doubt, build it well.

— End of brief —
