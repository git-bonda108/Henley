"""Fusion5 brand tokens and CSS injection."""

from pathlib import Path

CSS_PATH = Path(__file__).resolve().parent.parent / "theme" / "fusion5.css"

COLORS = {
    "grape": "#2A1A3D",
    "grape_deep": "#1A0F2E",
    "grape_soft": "#4A2F6B",
    "orange": "#FF6B1A",
    "orange_warm": "#FF8847",
    "orange_deep": "#E04A00",
    "cream": "#FFF8F2",
    "paper": "#FAF3EB",
    "ink": "#1A0F2E",
    "ink_muted": "#5A4F6B",
    "line": "#E8DFD2",
    "success": "#2D8659",
    "warning": "#D97706",
    "danger": "#B91C3C",
}


def load_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def inject_theme() -> None:
    import streamlit as st

    st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)


def hero_headline() -> None:
    import streamlit as st

    st.markdown(
        """
        <div class="f5-hero">
            <div class="f5-hero-grid">
                <div class="f5-hero-copy">
                    <p class="f5-eyebrow">Fusion5 · Henley Homes</p>
                    <h1 class="f5-display">
                        go beyond <span class="f5-accent">the manual quote comparison.</span>
                    </h1>
                    <p class="f5-lead">
                        An AI agent that compares a competitor home-builder quote against Henley's
                        equivalent — flags ambiguity, surfaces value, never fabricates a number.
                    </p>
                </div>
                <div class="f5-hero-mark" aria-hidden="true">
                    <div class="f5-infinity-cycle"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def internal_banner(session_id: str, generated_at: str) -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="f5-internal-banner">
            <strong>INTERNAL — Sales team review required</strong>
            · Generated {generated_at} · Session <code>{session_id}</code>
            <br><span class="f5-internal-sub">
            This is not customer-facing content. Review before any customer communication.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def session_footer(session_id: str | None) -> None:
    import streamlit as st

    sid = session_id or "—"
    st.markdown(
        f"""
        <div class="f5-footer">
            Session <code>{sid}</code> · Isolated comparison — no cross-session data (NFR-02)
        </div>
        """,
        unsafe_allow_html=True,
    )


def animated_vs_title(competitor: str, henley: str) -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="f5-vs-title">
            <span class="f5-vs-left">{competitor}</span>
            <span class="f5-vs-dot">vs</span>
            <span class="f5-vs-right">{henley}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_pill(level: str) -> str:
    cls = {"HIGH": "f5-pill-high", "MEDIUM": "f5-pill-medium", "LOW": "f5-pill-low"}.get(
        level.upper(), "f5-pill-medium"
    )
    return f'<span class="f5-pill {cls}">{level.upper()}</span>'
