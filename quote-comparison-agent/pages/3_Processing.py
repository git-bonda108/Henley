import time

import streamlit as st

from components.brand import animated_vs_title, inject_theme, session_footer
from components.session import ensure_session, init_session_state
from lib.agent.llm import get_provider
from lib.agent.pipeline import AGENT_NARRATION, PIPELINE_STEPS, run_pipeline

init_session_state()
inject_theme()
ensure_session()

w = st.session_state.wizard
competitor = w.get("competitor_brand") or "Competitor"
if w.get("competitor_brand") == "Other" and w.get("competitor_brand_other"):
    competitor = w["competitor_brand_other"]

st.title("Agent Processing")
animated_vs_title(competitor, "Builder Allegra 355-D38")

if not w.get("competitor_pdf") and not get_provider() == "demo":
    st.warning("No inputs found. Start from **New Comparison**.")
    if st.button("Go to wizard"):
        st.switch_page("pages/2_New_Comparison.py")
    st.stop()

# Run pipeline once
if not st.session_state.processing_complete and not st.session_state.get("ingest_result"):
    log_box = st.empty()
    logs: list[str] = []

    def on_log(msg: str) -> None:
        logs.append(msg)

    progress = st.progress(0, text="Starting agent…")
    with st.status("Running comparison pipeline…", expanded=True) as status:
        for i, step in enumerate(PIPELINE_STEPS[:7]):
            st.write(f"▸ **{step}**")
            st.caption(AGENT_NARRATION[i])
            progress.progress((i + 1) / len(PIPELINE_STEPS), text=step)
            time.sleep(0.35 if get_provider() == "demo" else 0.1)

        result = run_pipeline(w, on_log)
        st.session_state.ingest_result = result.extract.model_dump()
        st.session_state.ambiguities = [a.model_dump() for a in result.ambiguities]
        st.session_state.pipeline_logs = result.logs + logs
        if result.summary:
            st.session_state.summary = result.summary.model_dump()
        st.session_state.processing_complete = True
        status.update(label="Pipeline complete", state="complete")

    st.session_state.pipeline_step = 7 if st.session_state.ambiguities else len(PIPELINE_STEPS)

col_l, col_r = st.columns([2, 3])

with col_l:
    st.subheader("Agent timeline")
    step_idx = st.session_state.get("pipeline_step", 0)
    paused_at = 7 if st.session_state.ambiguities and not st.session_state.review_complete else -1

    for i, label in enumerate(PIPELINE_STEPS):
        if i < step_idx:
            dot, state = "qi-step-done", "complete"
        elif i == step_idx:
            dot, state = "qi-step-active", "active"
        elif i == paused_at:
            dot, state = "qi-step-paused", "paused"
        else:
            dot, state = "qi-step-pending", "pending"
        st.markdown(
            f'<div class="qi-timeline-step"><div class="qi-step-dot {dot}"></div><div>{label}</div></div>',
            unsafe_allow_html=True,
        )

with col_r:
    st.subheader("Live log")
    for line in st.session_state.get("pipeline_logs", []):
        st.markdown(f"*{line}*")

    if st.session_state.ambiguities and not st.session_state.review_complete:
        st.warning("Ambiguity detected — human confirmation required before summary.")
        if st.button("Review flagged items →", type="primary"):
            st.switch_page("pages/4_Review.py")
    elif st.session_state.processing_complete:
        if not st.session_state.summary:
            if st.session_state.review_complete or not st.session_state.ambiguities:
                from lib.schema.models import ExtractResult
                from lib.agent.pipeline import generate_summary

                extract = ExtractResult.model_validate(st.session_state.ingest_result)
                summary = generate_summary(w, extract, st.session_state.get("resolved_ambiguities", []))
                st.session_state.summary = summary.model_dump()
        if st.session_state.summary:
            if st.button("View summary →", type="primary"):
                st.switch_page("pages/5_Summary.py")

session_footer(st.session_state.session_id)
