import streamlit as st

from components.brand import hero_headline, inject_theme, session_footer
from components.session import ensure_session, init_session_state, reset_comparison

init_session_state()
inject_theme()
ensure_session()

hero_headline()

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Start a comparison →", type="primary", use_container_width=True):
        reset_comparison()
        st.switch_page("pages/2_New_Comparison.py")
with col2:
    st.button("See how it works", use_container_width=True)

st.markdown("---")

c1, c2, c3 = st.columns([5, 4, 3])
cards = [
    ("Grounded in evidence", "Every figure traces to a source line. No hallucinations."),
    ("Pauses for ambiguity", 'When a competitor says "downlights included" with no quantity, the agent asks before comparing.'),
    ("Internal only", "The agent produces an internal summary. The sales team owns the customer email."),
]
for col, (title, body) in zip([c1, c2, c3], cards):
    with col:
        st.markdown(
            f'<div class="qi-principle-card"><h3>{title}</h3><p>{body}</p></div>',
            unsafe_allow_html=True,
        )

session_footer(st.session_state.session_id)
