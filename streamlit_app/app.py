import streamlit as st

st.set_page_config(
    page_title="Walmart Executive KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Walmart Executive KPI Dashboard")
st.markdown(
    """
    Welcome to the executive dashboard.

    Use the pages in the left sidebar to explore:
    - Executive Overview
    - Drivers
    - Store Performance
    - Holiday / Seasonality
    - Metric Dictionary
    """
)

st.info("Select a page from the sidebar to begin.")