"""
Walmart Weekly Sales — Page 1: Executive KPIs
=============================================
Run:
    streamlit run page1_executive_kpis.py

Requirements:
    pip install streamlit pandas plotly

Place raw_sales.csv and raw_stores.csv in the same directory,
or adjust DATA_DIR below.
"""

import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.dirname(__file__)
SALES_FILE  = os.path.join(DATA_DIR, "raw_sales.csv")
STORES_FILE = os.path.join(DATA_DIR, "raw_stores.csv")

BLUE        = "#1A73E8"
DARK_BLUE   = "#0D47A1"
AMBER       = "#E37400"
GREEN       = "#137333"
RED         = "#C5221F"
LIGHT_GRAY  = "#F8F9FA"
BORDER      = "#DADCE0"

st.set_page_config(
    page_title="Walmart Executive KPIs",
    page_icon="🛒",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide default Streamlit header/footer */
    #MainMenu, footer, header { visibility: visible; }

    /* Top banner */
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
    .top-banner h2 { margin: 0; font-size: 16px; font-weight: 500; }
    .top-banner span { font-size: 20px; opacity: 0.85; }

    /* KPI tiles */
    .kpi-block {
        background: white;
        border: 1px solid #DADCE0;
        border-radius: 10px;
        padding: 14px 18px;
    }
    .kpi-label {
        font-size: 14px;
        color: #5F6368;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 500;
        color: #202124;
        line-height: 1;
    }
    .kpi-delta-pos { font-size: 12px; color: #137333; margin-top: 5px; }
    .kpi-delta-neg { font-size: 12px; color: #C5221F; margin-top: 5px; }
    .kpi-delta-neu { font-size: 12px; color: #5F6368; margin-top: 5px; }

    /* Chart cards */
    .chart-title {
        font-size: 11px;
        font-weight: 500;
        color: #5F6368;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }

    /* Divider */
    hr { border-top: 1px solid #DADCE0; margin: 8px 0 16px 0; }

    /* Reduce default Streamlit padding */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data…")
def load_data():
    sales  = pd.read_csv(SALES_FILE)
    stores = pd.read_csv(STORES_FILE)

    sales.columns  = sales.columns.str.strip()
    stores.columns = stores.columns.str.strip()

    sales["Date"]         = pd.to_datetime(sales["Date"])
    sales["week_start"]   = sales["Date"] - pd.to_timedelta(sales["Date"].dt.dayofweek, unit="d")
    sales["IsHoliday"]    = sales["IsHoliday"].astype(str).str.upper().map({"TRUE": True, "FALSE": False})
    sales["Weekly_Sales"] = pd.to_numeric(sales["Weekly_Sales"], errors="coerce")

    df = sales.merge(stores, on="Store", how="left")
    return df


df_raw = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")

    store_types = sorted(df_raw["Type"].dropna().unique())
    selected_types = st.multiselect(
        "Store Type", store_types, default=store_types,
        help="Filter by store type (A / B / C)"
    )

    min_date = df_raw["week_start"].min().date()
    max_date = df_raw["week_start"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    holiday_filter = st.radio(
        "Holiday Weeks",
        options=["All weeks", "Holiday only", "Non-holiday only"],
        index=0,
    )

    st.markdown("---")
    st.caption("Data: Walmart Store Sales 2010–2012")
    st.divider(width = "stretch")
    
    st.caption(
    """
    <div class="footer" style="text-align:left; line-height:1.6;">
        <div>Created by: <b>Sina Shariati</b>
        | Contact: <a href="https://www.linkedin.com/in/sina-shariati-5a26227a/" target="_blank">LinkedIn</a></div>
        <div>Business Intelligence Analyst</div>
        <div>Copyright © 2026 | All rights reserved.</div>
    </div>
    """,
    unsafe_allow_html=True
)


# ── Apply Filters ─────────────────────────────────────────────────────────────
df = df_raw.copy()

if selected_types:
    df = df[df["Type"].isin(selected_types)]

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
    df = df[(df["week_start"].dt.date >= start_d) & (df["week_start"].dt.date <= end_d)]

if holiday_filter == "Holiday only":
    df = df[df["IsHoliday"] == True]
elif holiday_filter == "Non-holiday only":
    df = df[df["IsHoliday"] == False]


# ── Aggregations ──────────────────────────────────────────────────────────────

# Weekly totals
weekly = (
    df.groupby("week_start")
    .agg(
        total_sales=("Weekly_Sales", "sum"),
        active_stores=("Store", "nunique"),
        is_holiday=("IsHoliday", "max"),
    )
    .reset_index()
    .sort_values("week_start")
)

weekly["sales_per_store"] = weekly["total_sales"] / weekly["active_stores"]
weekly["wow_growth"]      = weekly["total_sales"].pct_change()
weekly["yoy_growth"]      = weekly["total_sales"].pct_change(periods=52)
weekly["ma4"]             = weekly["total_sales"].rolling(4, min_periods=1).mean()
weekly["rolling_std8"]    = weekly["total_sales"].rolling(8, min_periods=2).std()
weekly["rolling_avg8"]    = weekly["total_sales"].rolling(8, min_periods=2).mean()
weekly["volatility_cv"]   = weekly["rolling_std8"] / weekly["rolling_avg8"]

# Holiday lift
h_avg   = df[df["IsHoliday"] == True]["Weekly_Sales"].mean()
nh_avg  = df[df["IsHoliday"] == False]["Weekly_Sales"].mean()
holiday_lift = (h_avg - nh_avg) / nh_avg if nh_avg and nh_avg != 0 else 0

# Store-type weekly
type_weekly = (
    df.groupby(["week_start", "Type"])["Weekly_Sales"]
    .sum()
    .reset_index()
    .rename(columns={"Weekly_Sales": "sales"})
)
type_totals = df.groupby("Type")["Weekly_Sales"].sum().reset_index()

# Department holiday lift
dept_lift_raw = (
    df.groupby(["Dept", "IsHoliday"])["Weekly_Sales"]
    .mean()
    .reset_index()
)
dept_holiday    = dept_lift_raw[dept_lift_raw["IsHoliday"] == True].rename(columns={"Weekly_Sales": "holiday_avg"}).drop(columns="IsHoliday")
dept_nonholiday = dept_lift_raw[dept_lift_raw["IsHoliday"] == False].rename(columns={"Weekly_Sales": "non_holiday_avg"}).drop(columns="IsHoliday")
dept_lift = dept_holiday.merge(dept_nonholiday, on="Dept", how="inner")
dept_lift["lift_pct"] = (dept_lift["holiday_avg"] - dept_lift["non_holiday_avg"]) / dept_lift["non_holiday_avg"]
top_dept_lift = dept_lift.nlargest(5, "lift_pct")

# Latest week KPIs
latest = weekly.iloc[-1]
prev   = weekly.iloc[-2] if len(weekly) > 1 else latest

total_sales_latest = latest["total_sales"]
active_stores_latest = int(latest["active_stores"])
sales_per_store_latest = latest["sales_per_store"]
wow = latest["wow_growth"]
yoy = latest["yoy_growth"]


# ── Header Banner ─────────────────────────────────────────────────────────────
latest_week_str = latest["week_start"].strftime("%b %d, %Y")
st.markdown(f"""
<div class="top-banner">
  <h2>🛒 Walmart Weekly Sales — Executive KPIs</h2>
  <span>Week of {latest_week_str} &nbsp;|&nbsp; Stores: {", ".join(selected_types) if selected_types else "None"}</span>
</div>
""", unsafe_allow_html=True)


# ── KPI Tiles ─────────────────────────────────────────────────────────────────
def fmt_delta(val, pct=True):
    if pd.isna(val):
        return "neu", "N/A"
    arrow = "▲" if val > 0 else "▼"
    css   = "pos" if val > 0 else "neg"
    label = f"{arrow} {val*100:+.1f}%" if pct else f"{arrow} {val:+,.0f}"
    return css, label

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    delta_css, delta_label = fmt_delta(wow)
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Total Weekly Sales</div>
      <div class="kpi-value">${total_sales_latest/1e6:.1f}M</div>
      <div class="kpi-delta-{delta_css}">{delta_label} WoW</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Active Stores</div>
      <div class="kpi-value">{active_stores_latest}</div>
      <div class="kpi-delta-neu">Unique stores this week</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Sales per Store</div>
      <div class="kpi-value">${sales_per_store_latest/1e6:.2f}M</div>
      <div class="kpi-delta-neu">Avg productivity / store</div>
    </div>""", unsafe_allow_html=True)

with k4:
    wow_css, wow_label = fmt_delta(wow)
    yoy_css, yoy_label = fmt_delta(yoy)
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">WoW Growth</div>
      <div class="kpi-value kpi-delta-{wow_css}">{wow*100:+.1f}%</div>
      <div class="kpi-delta-{yoy_css}">YoY {yoy_label}</div>
    </div>""", unsafe_allow_html=True)

with k5:
    lift_css = "pos" if holiday_lift > 0 else "neg"
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Holiday Lift</div>
      <div class="kpi-value">{holiday_lift*100:+.1f}%</div>
      <div class="kpi-delta-{lift_css}">Holiday vs non-holiday avg</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 2: Trend chart + Store Type bar ───────────────────────────────────────
col_trend, col_type = st.columns([2, 1])

with col_trend:
    st.markdown('<div class="chart-title">Total Weekly Sales Trend &amp; 4-Week Moving Average</div>', unsafe_allow_html=True)

    fig_trend = go.Figure()

    # Area fill under main line
    fig_trend.add_trace(go.Scatter(
        x=weekly["week_start"], y=weekly["total_sales"],
        fill="tozeroy",
        fillcolor="rgba(26,115,232,0.08)",
        line=dict(color=BLUE, width=2.5),
        name="Weekly Sales",
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Sales: $%{y:,.0f}<extra></extra>",
    ))

    # MA4 dashed overlay
    fig_trend.add_trace(go.Scatter(
        x=weekly["week_start"], y=weekly["ma4"],
        line=dict(color=AMBER, width=2, dash="dot"),
        name="4W Moving Avg",
        hovertemplate="MA4: $%{y:,.0f}<extra></extra>",
    ))

    # Holiday markers
    holiday_weeks = weekly[weekly["is_holiday"] == True]
    fig_trend.add_trace(go.Scatter(
        x=holiday_weeks["week_start"],
        y=holiday_weeks["total_sales"],
        mode="markers",
        marker=dict(symbol="diamond", size=8, color=GREEN, line=dict(color="white", width=1)),
        name="Holiday Week",
        hovertemplate="Holiday: $%{y:,.0f}<extra></extra>",
    ))

    fig_trend.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        xaxis=dict(showgrid=False, tickfont=dict(size=10), linecolor=BORDER),
        yaxis=dict(
            showgrid=True, gridcolor=BORDER, tickfont=dict(size=10),
            tickformat="$,.0f", linecolor=BORDER,
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_type:
    st.markdown('<div class="chart-title">Sales by Store Type</div>', unsafe_allow_html=True)

    fig_type = go.Figure(go.Bar(
        x=type_totals["Weekly_Sales"],
        y=type_totals["Type"],
        orientation="h",
        marker_color=[BLUE, "#4285F4", "#8AB4F8"][:len(type_totals)],
        text=[f"${v/1e6:.1f}M" for v in type_totals["Weekly_Sales"]],
        textposition="outside",
        hovertemplate="Type %{y}: $%{x:,.0f}<extra></extra>",
    ))
    fig_type.update_layout(
        height=280,
        margin=dict(l=0, r=60, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor=BORDER, tickformat="$,.0f", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=12)),
        showlegend=False,
    )
    st.plotly_chart(fig_type, use_container_width=True)


st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 3: YoY growth | Volatility | Holiday lift by dept ────────────────────
col_yoy, col_vol, col_hlift = st.columns(3)

with col_yoy:
    st.markdown('<div class="chart-title">YoY Growth %</div>', unsafe_allow_html=True)

    yoy_data = weekly.dropna(subset=["yoy_growth"])
    colors_yoy = [GREEN if v >= 0 else RED for v in yoy_data["yoy_growth"]]

    fig_yoy = go.Figure()
    fig_yoy.add_hline(y=0, line_width=1, line_dash="dot", line_color=BORDER)
    fig_yoy.add_trace(go.Scatter(
        x=yoy_data["week_start"],
        y=yoy_data["yoy_growth"] * 100,
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(19,115,51,0.07)",
        line=dict(color=GREEN, width=2),
        name="YoY Growth",
        hovertemplate="%{x|%b %d %Y}<br>YoY: %{y:.1f}%<extra></extra>",
    ))
    fig_yoy.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=9), linecolor=BORDER),
        yaxis=dict(showgrid=True, gridcolor=BORDER, ticksuffix="%", tickfont=dict(size=9)),
        hovermode="x unified",
    )
    st.plotly_chart(fig_yoy, use_container_width=True)

with col_vol:
    st.markdown('<div class="chart-title">Volatility Index (CV) — 8W Rolling</div>', unsafe_allow_html=True)

    vol_data = weekly.dropna(subset=["volatility_cv"])
    cv_threshold = 0.20

    fig_vol = go.Figure()
    fig_vol.add_hline(
        y=cv_threshold, line_width=1.2, line_dash="dot", line_color=AMBER,
        annotation_text="Threshold 0.20", annotation_font_size=9,
        annotation_position="bottom right",
    )
    fig_vol.add_trace(go.Scatter(
        x=vol_data["week_start"],
        y=vol_data["volatility_cv"],
        fill="tozeroy",
        fillcolor="rgba(26,115,232,0.07)",
        line=dict(color=BLUE, width=2),
        name="CV",
        hovertemplate="%{x|%b %d %Y}<br>CV: %{y:.3f}<extra></extra>",
    ))
    fig_vol.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=9), linecolor=BORDER),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(size=9)),
        hovermode="x unified",
    )
    st.plotly_chart(fig_vol, use_container_width=True)

with col_hlift:
    st.markdown('<div class="chart-title">Holiday Lift % — Top 5 Departments</div>', unsafe_allow_html=True)

    top = top_dept_lift.sort_values("lift_pct")

    fig_hl = go.Figure(go.Bar(
        x=top["lift_pct"] * 100,
        y=top["Dept"].astype(str),
        orientation="h",
        marker=dict(
            color=top["lift_pct"] * 100,
            colorscale=[[0, "#CEEAD6"], [1, "#137333"]],
            showscale=False,
        ),
        text=[f"+{v*100:.1f}%" for v in top["lift_pct"]],
        textposition="outside",
        hovertemplate="Dept %{y}<br>Holiday lift: %{x:.1f}%<extra></extra>",
    ))
    fig_hl.update_layout(
        height=220,
        margin=dict(l=0, r=50, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(
            showgrid=True, gridcolor=BORDER, ticksuffix="%",
            tickfont=dict(size=9), linecolor=BORDER,
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_hl, use_container_width=True)
