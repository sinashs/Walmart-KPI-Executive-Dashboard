import os
import streamlit as st

st.set_page_config(
    page_title="Walmart Metric Dictionary",
    page_icon="📘",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
METRIC_FILE = os.path.join(BASE_DIR, "metric_dictionary.md")

st.markdown("""
<style>
    .top-banner {
        background: #0D47A1;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .top-banner h2 {
        margin: 0;
        font-size: 16px;
        font-weight: 500;
    }
    .top-banner span {
        font-size: 20px;
        opacity: 0.85;
    }
    .info-card {
        background: white;
        border: 1px solid #DADCE0;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-banner">
  <h2>📘 Walmart Weekly Sales — Metric Dictionary</h2>
  <span>Definitions • Formulas • Assumptions • Governance</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-card">
    <b>Purpose</b><br>
    This page documents the business definitions, formulas, assumptions, and governance checks
    used across the Walmart Weekly Sales dashboard pages. Use it as the single source of truth
    for KPI interpretation.
</div>
""", unsafe_allow_html=True)

if os.path.exists(METRIC_FILE):
    with open(METRIC_FILE, "r", encoding="utf-8") as f:
        metric_text = f.read()
    st.markdown(metric_text)
else:
    st.error("metric_dictionary.md was not found in the project root.")