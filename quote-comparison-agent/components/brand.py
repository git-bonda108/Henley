"""Quote Intelligence brand tokens and CSS injection."""

from pathlib import Path

CSS_PATH = Path(__file__).resolve().parent.parent / "theme" / "quote_intelligence.css"

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
        <div class="qi-hero">
            <div class="qi-hero-grid">
                <div class="qi-hero-copy">
                    <p class="qi-eyebrow">Quote Intelligence</p>
                    <h1 class="qi-display">
                        go beyond <span class="qi-accent">the manual quote comparison.</span>
                    </h1>
                    <p class="qi-lead">
                        An AI agent that compares a competitor home-builder quote against Builder's
                        equivalent — flags ambiguity, surfaces value, never fabricates a number.
                    </p>
                </div>
                <div class="qi-hero-mark" aria-hidden="true">
                    <div class="qi-infinity-cycle"></div>
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
        <div class="qi-internal-banner">
            <strong>INTERNAL — Sales team review required</strong>
            · Generated {generated_at} · Session <code>{session_id}</code>
            <br><span class="qi-internal-sub">
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
        <div class="qi-footer">
            Session <code>{sid}</code> · Isolated comparison — no cross-session data (NFR-02)
        </div>
        """,
        unsafe_allow_html=True,
    )


def animated_vs_title(competitor: str, builder: str) -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="qi-vs-title">
            <span class="qi-vs-left">{competitor}</span>
            <span class="qi-vs-dot">vs</span>
            <span class="qi-vs-right">{builder}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_pill(level: str) -> str:
    cls = {"HIGH": "qi-pill-high", "MEDIUM": "qi-pill-medium", "LOW": "qi-pill-low"}.get(
        level.upper(), "qi-pill-medium"
    )
    return f'<span class="qi-pill {cls}">{level.upper()}</span>'
