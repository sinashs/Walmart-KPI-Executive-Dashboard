"""
Walmart Weekly Sales — Multi-Page Dashboard
============================================
Entry point. Run with:

    streamlit run app.py

Required files (all in the same directory as app.py):
    page1_executive_kpis.py
    page2_top_movers.py
    page3_at_risk.py
    page4_metric_dictionary.py
    raw_sales.csv
    raw_stores.csv
    metric_dictionary.md
    Walmart-Logo.jpg

Streamlit >= 1.36 is required for st.navigation / st.Page.
Install / upgrade: pip install --upgrade streamlit
"""

import base64
import os
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOGO_FILE = os.path.join(BASE_DIR, "Walmart-Logo.jpg")

# ── Page config  (must be the very first Streamlit call) ──────────────────────
st.set_page_config(
    page_title="Walmart Sales Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide Streamlit's default top chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Full-width logo banner ── */
    .logo-header {
        display: flex;
        align-items: center;
        gap: 18px;
        background: #0D47A1;
        border-radius: 12px;
        padding: 10px 20px;
        margin-bottom: 14px;
    }
    .logo-header img {
        height: 44px;
        border-radius: 6px;
        background: white;
        padding: 4px 8px;
        object-fit: contain;
    }
    .logo-header-text { color: white; }
    .logo-header-text h1 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        letter-spacing: .2px;
        line-height: 1.2;
    }
    .logo-header-text p { margin: 0; font-size: 11px; opacity: .8; }

    /* ── Sidebar logo ── */
    .sidebar-logo { text-align: center; padding: 8px 0 4px 0; }
    .sidebar-logo img { width: 82%; border-radius: 6px; }

    .block-container { padding-top: .75rem; padding-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)


# ── Logo helpers ──────────────────────────────────────────────────────────────
def _logo_b64() -> str:
    """Return the Walmart logo as a base64 data-URI, or empty string if missing."""
    if not os.path.exists(LOGO_FILE):
        return ""
    with open(LOGO_FILE, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


# Sidebar logo — rendered once by app.py and visible on every page
with st.sidebar:
    src = _logo_b64()
    if src:
        st.markdown(
            f'<div class="sidebar-logo"><img src="{src}" alt="Walmart logo"></div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")


# ── Page definitions ──────────────────────────────────────────────────────────
#
#   st.Page(path) tells Streamlit to execute the given .py file as its own
#   isolated page. Each file keeps its own set_page_config, data loading,
#   sidebar widgets, and chart rendering — nothing is imported or modified.
#
#   The only requirement is that set_page_config inside each page file is
#   *not* called when running under st.navigation (Streamlit ignores duplicate
#   calls gracefully in >= 1.36).
#
pg1 = st.Page(
    os.path.join(BASE_DIR, "pages/page1_executive_kpis.py"),
    title="Executive KPIs",
    icon="📊",
    default=True,                   # landing page when the app first opens
)
pg2 = st.Page(
    os.path.join(BASE_DIR, "pages/page2_top_movers.py"),
    title="Top Movers",
    icon="📈",
)
pg3 = st.Page(
    os.path.join(BASE_DIR, "pages/page3_at_risk.py"),
    title="At-Risk Stores",
    icon="⚠️",
)
pg4 = st.Page(
    os.path.join(BASE_DIR, "pages/page4_metric_dictionary.py"),
    title="Metric Dictionary",
    icon="📘",
)

pg5 = st.Page(
    os.path.join(BASE_DIR, "pages/page5_insights.py"),
    title="Key Insights",
    icon="💡",
)

# ── Navigation ────────────────────────────────────────────────────────────────
#
#   Pages are grouped into two sections in the sidebar:
#     • Insights   — executive summary and key takeaways
#     • Dashboard  — the three analytical pages
#     • Reference  — the metric dictionary
#
#   st.navigation renders the menu and returns the selected Page object.
#   Calling .run() on it executes that page's script in place.
#
pg = st.navigation(
    {
        "Insights":  [pg5],
        "Dashboard": [pg1, pg2, pg3],
        "Reference": [pg4],
    },
    position="sidebar",
    expanded=True,
)

pg.run()

# ------------------------- Footer -------------------------   
st.divider(width = "stretch")
cols = st.columns(1)[0]
with cols:
    st.markdown(
    """
    <div class="footer" style="text-align:center; line-height:1.6;">
        <div>Created by: <b>Sina Shariati</b>
        | Contact: <a href="https://www.linkedin.com/in/sina-shariati-5a26227a/" target="_blank">LinkedIn</a></div>
        <div>Business Intelligence Analyst</div>
        <div>Copyright © 2026 | All rights reserved.</div>
    </div>
    """,
    unsafe_allow_html=True
)