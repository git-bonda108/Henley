import streamlit as st

from components.brand import inject_theme, internal_banner, session_footer
from components.session import ensure_session, init_session_state, reset_comparison
from lib.agent.pipeline import generate_summary
from lib.export import to_docx_bytes, to_markdown, to_pdf_bytes
from lib.schema.models import ComparisonSummary, ExtractResult


def _render_header(s: ComparisonSummary) -> None:
    h = s.header
    st.markdown(
        f"""
        | | |
        |---|---|
        | Henley plan | **{h.henley_plan}** |
        | Competitor | **{h.competitor_builder} — {h.competitor_plan}** |
        | Region | {h.region} |
        | Sales rep | {h.sales_rep} |
        | Run date | {h.run_date} |
        """
    )


def _render_bullets(items: list) -> None:
    for item in items:
        point = item.get("point", str(item))
        st.markdown(f"- {point}")
        if st.session_state.show_source_evidence and item.get("source"):
            st.caption(f'Source: {item["source"]}')


def _render_inclusion_matrix(s: ComparisonSummary) -> None:
    import pandas as pd

    rows = [
        {"Category": r.category, "Henley": r.henley, "Competitor": r.competitor, "Advantage": r.advantage}
        for r in s.inclusion_differences
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_value_list(items, kind: str) -> None:
    border = "var(--f5-success)" if kind == "henley" else "var(--f5-warning)"
    for v in items:
        val = f"${v.value:,.0f}" if v.value is not None else "Unconfirmed"
        chip = f'<span class="f5-source-chip">{v.source_ref}</span>' if v.source_ref else ""
        st.markdown(
            f'<div style="border-left:3px solid {border};padding-left:0.75rem;margin-bottom:0.5rem;">'
            f'{v.point} — <span class="f5-mono">{val}</span>{chip}</div>',
            unsafe_allow_html=True,
        )


def _render_reconciliation(s: ComparisonSummary) -> None:
    import pandas as pd

    q = s.quote_reconciliation
    rows = [
        {"Description": r.description, "Competitor +": r.competitor_add, "Henley +": r.henley_add, "Ref": r.source_ref}
        for r in q.rows
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown(
        f"**Current:** Competitor ${q.current_price_competitor or 0:,.0f} · Henley ${q.current_price_henley or 0:,.0f}"
    )


def _render_flags(s: ComparisonSummary) -> None:
    for f in s.flagged_items:
        st.markdown(f"**{f.get('itemName')}** · {f.get('confidence', 'LOW')}")
        st.write(f.get("reason"))
        st.caption(f.get("suggestedClarification"))


def _render_questions(s: ComparisonSummary) -> None:
    for q in s.open_questions:
        st.markdown(f"- {q}")


init_session_state()
inject_theme()
ensure_session()

w = st.session_state.wizard

if not st.session_state.get("summary"):
    if st.session_state.get("ingest_result"):
        extract = ExtractResult.model_validate(st.session_state.ingest_result)
        summary = generate_summary(w, extract, st.session_state.get("resolved_ambiguities", []))
        st.session_state.summary = summary.model_dump()
    else:
        st.warning("No comparison data. Start a new comparison.")
        if st.button("New comparison"):
            st.switch_page("pages/2_New_Comparison.py")
        st.stop()

summary = ComparisonSummary.model_validate(st.session_state.summary)
sid = st.session_state.session_id

internal_banner(sid, summary.header.run_date)

if summary.headline_advantage is not None:
    st.markdown(
        f'<div class="f5-headline-number"><span>$</span>{summary.headline_advantage:,.0f}</div>'
        '<p style="color:var(--f5-ink-muted);margin-top:0;">Confirmed Henley value advantage (where directly comparable)</p>',
        unsafe_allow_html=True,
    )

st.session_state.show_source_evidence = st.toggle(
    "Show source evidence", st.session_state.get("show_source_evidence", False)
)

sections = [
    ("1", "Header", lambda: _render_header(summary)),
    ("2", "Headline Snapshot", lambda: st.write(summary.headline_snapshot)),
    ("3", "Design Differences", lambda: _render_bullets(summary.design_differences)),
    ("4", "Inclusion Differences", lambda: _render_inclusion_matrix(summary)),
    ("5", "Henley Value Advantage", lambda: _render_value_list(summary.henley_value_advantage, "henley")),
    ("6", "Competitor Advantage / Gaps", lambda: _render_value_list(summary.competitor_advantage_gaps, "gap")),
    ("7", "Quote Reconciliation", lambda: _render_reconciliation(summary)),
    ("8", "Flagged Items", lambda: _render_flags(summary)),
    ("9", "Open Questions", lambda: _render_questions(summary)),
]

nav_col, content_col = st.columns([1, 3])
with nav_col:
    st.markdown("**Sections**")
    for num, title, _ in sections:
        st.markdown(f"{num}. {title}")

with content_col:
    for num, title, renderer in sections:
        with st.expander(f"{num}. {title}", expanded=num in ("1", "2", "8")):
            renderer()

    if summary.conditionals.promotional_adjustments:
        with st.expander("C3. Promotional Adjustments"):
            for p in summary.conditionals.promotional_adjustments:
                st.markdown(f"- {p}")
    if summary.conditionals.energy_compliance_note:
        with st.expander("C4. Energy / 7-Star Compliance"):
            st.write(summary.conditionals.energy_compliance_note)

st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
md = to_markdown(summary, sid)
with c1:
    st.download_button(
        "Export PDF", to_pdf_bytes(summary, sid), file_name=f"{sid}.pdf", mime="application/pdf", use_container_width=True
    )
with c2:
    st.download_button(
        "Export DOCX",
        to_docx_bytes(summary, sid),
        file_name=f"{sid}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )
with c3:
    st.download_button("Copy Markdown", md, file_name=f"{sid}.md", mime="text/markdown", use_container_width=True)
with c4:
    if st.button("New comparison", use_container_width=True):
        reset_comparison()
        st.switch_page("pages/2_New_Comparison.py")

session_footer(sid)
