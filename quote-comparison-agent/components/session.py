"""Session bootstrap and shared Streamlit state."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import streamlit as st

SESSION_DEFAULTS: dict[str, Any] = {
    "session_id": None,
    "wizard": {
        "competitor_pdf": None,
        "competitor_pdf_name": "",
        "competitor_brand": "Carlisle Homes",
        "competitor_brand_other": "",
        "henley_pdf": None,
        "henley_pdf_name": "",
        "competitor_url": "",
        "henley_url": "",
        "region": "VIC",
        "sales_rep": "",
        "customer_ref": "",
        "promotions": [],
    },
    "ingest_result": None,
    "pipeline_step": 0,
    "pipeline_logs": [],
    "ambiguities": [],
    "resolved_ambiguities": [],
    "current_ambiguity_idx": 0,
    "summary": None,
    "processing_complete": False,
    "review_complete": False,
    "show_source_evidence": False,
}


def init_session_state() -> None:
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default.copy() if isinstance(default, dict) else default


def new_session_id() -> str:
    return f"QCP-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8].upper()}"


def reset_comparison() -> None:
    for key, default in SESSION_DEFAULTS.items():
        st.session_state[key] = default.copy() if isinstance(default, dict) else default
    st.session_state.session_id = new_session_id()


def ensure_session() -> str:
    if not st.session_state.get("session_id"):
        st.session_state.session_id = new_session_id()
    return st.session_state.session_id
