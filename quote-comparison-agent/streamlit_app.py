import config  # noqa: F401 — load .env first

import streamlit as st

from components.brand import inject_theme, session_footer
from components.session import ensure_session, init_session_state

st.set_page_config(
    page_title="Quote Comparison Agent",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_theme()

home = st.Page("pages/1_Home.py", title="Home", icon="🏠", default=True)
wizard = st.Page("pages/2_New_Comparison.py", title="New Comparison", icon="📋")
processing = st.Page("pages/3_Processing.py", title="Processing", icon="⚙️")
review = st.Page("pages/4_Review.py", title="Review", icon="✅")
summary = st.Page("pages/5_Summary.py", title="Summary", icon="📊")

pg = st.navigation([home, wizard, processing, review, summary])
pg.run()

with st.sidebar:
    st.markdown("---")
    provider = __import__("lib.agent.llm", fromlist=["get_provider"]).get_provider()
    st.caption(f"LLM: **{provider.upper()}**")
    ensure_session()
    session_footer(st.session_state.get("session_id"))
