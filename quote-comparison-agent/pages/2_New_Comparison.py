import streamlit as st

from components.brand import inject_theme, session_footer
from components.session import ensure_session, init_session_state
from lib.agent.llm import get_provider
from lib.ingestion.pdf import detect_brand, extract_pdf_text

init_session_state()
inject_theme()
ensure_session()

w = st.session_state.wizard

st.title("New Comparison")
st.caption("Upload both quotes, provide design URLs, and set run context. All four sections must be ready.")

# ── Section 1: Competitor quote ──────────────────────────────────────────────
with st.expander("1 · Competitor quote", expanded=True):
    status = "READY" if w.get("competitor_pdf") else "PENDING"
    st.markdown(f'<span class="f5-status-pill f5-status-{"ready" if status=="READY" else "pending"}">{status}</span>', unsafe_allow_html=True)

    comp_file = st.file_uploader("Competitor quote PDF (≤25 MB)", type=["pdf"], key="comp_pdf")
    if comp_file:
        w["competitor_pdf"] = comp_file.getvalue()
        w["competitor_pdf_name"] = comp_file.name
        meta = extract_pdf_text(w["competitor_pdf"])
        detected = detect_brand(meta["text"])
        st.success(f"**{comp_file.name}** · {meta['page_count']} pages · detected: {detected}")

    brand_opts = ["Carlisle Homes", "Metricon", "Other"]
    default_idx = brand_opts.index(w["competitor_brand"]) if w["competitor_brand"] in brand_opts else 0
    w["competitor_brand"] = st.radio("Detected competitor", brand_opts, index=default_idx, horizontal=True)
    if w["competitor_brand"] == "Other":
        w["competitor_brand_other"] = st.text_input("Builder name", w.get("competitor_brand_other", ""))

# ── Section 2: Henley quote ──────────────────────────────────────────────────
with st.expander("2 · Henley quote", expanded=bool(w.get("competitor_pdf"))):
    status = "READY" if w.get("henley_pdf") else "PENDING"
    st.markdown(f'<span class="f5-status-pill f5-status-{"ready" if status=="READY" else "pending"}">{status}</span>', unsafe_allow_html=True)

    hen_file = st.file_uploader("Henley quote PDF", type=["pdf"], key="hen_pdf")
    if hen_file:
        w["henley_pdf"] = hen_file.getvalue()
        w["henley_pdf_name"] = hen_file.name
        meta = extract_pdf_text(w["henley_pdf"])
        st.success(f"**{hen_file.name}** · {meta['page_count']} pages")

# ── Section 3: Home design URLs ────────────────────────────────────────────────
with st.expander("3 · Home design URLs", expanded=bool(w.get("henley_pdf"))):
    urls_ok = bool(w.get("competitor_url", "").startswith("http")) and bool(w.get("henley_url", "").startswith("http"))
    status = "READY" if urls_ok else "PENDING"
    st.markdown(f'<span class="f5-status-pill f5-status-{"ready" if status=="READY" else "pending"}">{status}</span>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        w["competitor_url"] = st.text_input(
            "Competitor home design URL",
            w.get("competitor_url") or "https://www.carlislehomes.com.au/home-designs/",
        )
    with c2:
        w["henley_url"] = st.text_input(
            "Henley home design URL",
            w.get("henley_url") or "https://www.henley.com.au/home-designs/",
        )
    st.caption("We re-fetch live on every run — no caching (FR-02.3).")

# ── Section 4: Run context ─────────────────────────────────────────────────────
with st.expander("4 · Run context", expanded=urls_ok):
    ctx_ok = bool(w.get("sales_rep", "").strip())
    status = "READY" if ctx_ok else "PENDING"
    st.markdown(f'<span class="f5-status-pill f5-status-{"ready" if status=="READY" else "pending"}">{status}</span>', unsafe_allow_html=True)

    w["region"] = st.radio("Region", ["VIC", "QLD", "NSW", "Other"], horizontal=True,
                             index=["VIC", "QLD", "NSW", "Other"].index(w.get("region", "VIC")))
    w["sales_rep"] = st.text_input("Sales rep name *", w.get("sales_rep", ""))
    w["customer_ref"] = st.text_input("Customer reference (optional)", w.get("customer_ref", ""))
    w["promotions"] = st.multiselect(
        "Active promotions",
        ["Sumitomo discount", "Battery/solar", "Other"],
        default=w.get("promotions", []),
    )

st.session_state.wizard = w

all_ready = all([
    w.get("competitor_url", "").startswith("http"),
    w.get("henley_url", "").startswith("http"),
    w.get("sales_rep", "").strip(),
]) and (
    (w.get("competitor_pdf") and w.get("henley_pdf"))
    or get_provider() == "demo"
)

st.markdown("---")
col_a, col_b = st.columns([2, 1])
with col_b:
    if st.button("Start comparison →", type="primary", disabled=not all_ready, use_container_width=True):
        st.session_state.pipeline_step = 0
        st.session_state.pipeline_logs = []
        st.session_state.processing_complete = False
        st.session_state.review_complete = False
        st.session_state.ambiguities = []
        st.session_state.resolved_ambiguities = []
        st.session_state.summary = None
        st.switch_page("pages/3_Processing.py")

if not all_ready:
    if get_provider() == "demo":
        st.info("Demo mode: PDFs optional. Provide URLs + sales rep name to run the canonical downlights fixture.")
    else:
        st.info("Complete all four sections to enable **Start comparison**.")

st.caption(f"Session `{st.session_state.session_id}` · Each comparison is isolated — no data carries over.")
session_footer(st.session_state.session_id)
