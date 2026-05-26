import streamlit as st

from components.brand import confidence_pill, inject_theme, session_footer
from components.session import ensure_session, init_session_state
from lib.schema.models import AmbiguityFlag

init_session_state()
inject_theme()
ensure_session()

flags = [AmbiguityFlag.model_validate(f) for f in st.session_state.get("ambiguities", [])]

if not flags:
    st.info("No ambiguities to review.")
    if st.button("Back to processing"):
        st.switch_page("pages/3_Processing.py")
    st.stop()

st.title("Human-in-the-Loop Review")
st.caption("Resolve each flagged item before the comparison summary is generated.")

idx = st.session_state.get("current_ambiguity_idx", 0)
if idx >= len(flags):
    st.session_state.review_complete = True
    st.session_state.pipeline_step = len(__import__("lib.agent.pipeline", fromlist=["PIPELINE_STEPS"]).PIPELINE_STEPS)
    from lib.schema.models import ExtractResult
    from lib.agent.pipeline import generate_summary

    extract = ExtractResult.model_validate(st.session_state.ingest_result)
    summary = generate_summary(st.session_state.wizard, extract, st.session_state.resolved_ambiguities)
    st.session_state.summary = summary.model_dump()
    st.success("All ambiguities resolved.")
    if st.button("View summary →", type="primary"):
        st.switch_page("pages/5_Summary.py")
    st.stop()

flag = flags[idx]
st.progress((idx) / len(flags), text=f"Item {idx + 1} of {len(flags)}")

st.markdown(
    f"""
    <div class="f5-ambiguity-card">
        <div>{confidence_pill(flag.confidence)} <strong>{flag.item_name}</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**COMPETITOR**")
    st.markdown(flag.competitor_wording)
    st.markdown(f"Price: **${flag.competitor_value or 0:,.0f}** · Quantity: **NOT SPECIFIED**")
with c2:
    st.markdown("**HENLEY**")
    st.markdown(flag.henley_detail)
    if flag.henley_value is not None:
        st.markdown(f'Price: <span class="f5-mono">${flag.henley_value:,.0f}</span>', unsafe_allow_html=True)

st.markdown("**Why this matters**")
st.write(flag.reason)

action = st.radio(
    "How should we treat this item?",
    [
        "Treat as comparable",
        "Flag as discussion point (don't compare directly)",
        "I have the competitor quantity",
    ],
    key=f"action_{flag.id}",
)

qty = None
if action == "I have the competitor quantity":
    qty = st.number_input("Competitor quantity", min_value=0, step=1, key=f"qty_{flag.id}")

with st.expander("+ Add a note for the sales team"):
    note = st.text_area("Note", key=f"note_{flag.id}", label_visibility="collapsed")

col_skip, col_confirm = st.columns([1, 1])
with col_skip:
    skip = st.button("Skip", use_container_width=True)
with col_confirm:
    confirm = st.button("Confirm →", type="primary", use_container_width=True)

if skip or confirm:
    action_map = {
        "Treat as comparable": "comparable",
        "Flag as discussion point (don't compare directly)": "discussion",
        "I have the competitor quantity": "quantity",
    }
    st.session_state.resolved_ambiguities.append({
        "flag_id": flag.id,
        "item_name": flag.item_name,
        "action": action_map[action],
        "quantity": qty,
        "note": note if confirm else "",
    })
    st.session_state.current_ambiguity_idx = idx + 1
    st.rerun()

session_footer(st.session_state.session_id)
