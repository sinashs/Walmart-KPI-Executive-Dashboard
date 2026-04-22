"""
Walmart Weekly Sales — Page 3: At-Risk Stores
==============================================
Run:
    streamlit run page3_at_risk.py

Requirements:
    pip install streamlit pandas plotly numpy

Place raw_sales.csv and raw_stores.csv in the same directory,
or adjust DATA_DIR below.
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR    = os.path.dirname(__file__)
SALES_FILE  = os.path.join(DATA_DIR, "raw_sales.csv")
STORES_FILE = os.path.join(DATA_DIR, "raw_stores.csv")

BLUE       = "#1A73E8"
DARK_BLUE  = "#0D47A1"
AMBER      = "#E37400"
GREEN      = "#137333"
RED        = "#C5221F"
RED_LIGHT  = "#E57368"
BORDER     = "#DADCE0"

RISK_HIGH_THRESHOLD = 20
RISK_MED_THRESHOLD  = 8

def risk_tier(score):
    if score >= RISK_HIGH_THRESHOLD:
        return "High"
    elif score >= RISK_MED_THRESHOLD:
        return "Medium"
    return "Low"

def tier_color(tier):
    return {"High": RED, "Medium": AMBER, "Low": GREEN}.get(tier, "#5F6368")

def tier_bg(tier):
    return {"High": "#FCE8E6", "Medium": "#FFF0D0", "Low": "#E6F4EA"}.get(tier, "#F8F9FA")


st.set_page_config(
    page_title="Walmart At-Risk Stores",
    page_icon="⚠️",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    #MainMenu, footer, header { visibility: visible; }

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
    .kpi-value { font-size: 26px; font-weight: 500; line-height: 1; }
    .kpi-sub   { font-size: 12px; color: #5F6368; margin-top: 5px; }

    .chart-title {
        font-size: 11px;
        font-weight: 500;
        color: #5F6368;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    hr { border-top: 1px solid #DADCE0; margin: 8px 0 16px 0; }
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
    sales["week_start"]   = sales["Date"] - pd.to_timedelta(
        sales["Date"].dt.dayofweek, unit="D"
    )
    sales["IsHoliday"]    = (
        sales["IsHoliday"].astype(str).str.upper()
        .map({"TRUE": True, "FALSE": False})
    )
    sales["Weekly_Sales"] = pd.to_numeric(sales["Weekly_Sales"], errors="coerce")

    df = sales.merge(stores, on="Store", how="left")
    return df


@st.cache_data(show_spinner="Scoring at-risk stores…")
def build_risk_scores(_df):
    """
    Replicates vw_at_risk_rankings.sql logic:
      risk_score = 50 * trend_decline + 30 * volatility + 20 * wow_decline
    Guards against inf / NaN from near-zero sales rows.
    """
    # Filter noisy near-zero rows before computing pct changes
    df = _df[_df["Weekly_Sales"] >= 100].copy()

    weekly = (
        df.groupby(["week_start", "Store", "Dept"])["Weekly_Sales"]
        .sum()
        .reset_index()
        .sort_values(["Store", "Dept", "week_start"])
    )

    # LAG values
    weekly["prev_week_sales"]  = weekly.groupby(["Store", "Dept"])["Weekly_Sales"].shift(1)
    weekly["prev_8week_sales"] = weekly.groupby(["Store", "Dept"])["Weekly_Sales"].shift(8)

    # Replace 0 denominators with NaN to avoid inf
    weekly["wow_change_pct"] = (
        (weekly["Weekly_Sales"] - weekly["prev_week_sales"])
        / weekly["prev_week_sales"].replace(0, np.nan)
    )
    weekly["trend_8w_pct"] = (
        (weekly["Weekly_Sales"] - weekly["prev_8week_sales"])
        / weekly["prev_8week_sales"].replace(0, np.nan)
    )

    # Rolling 8-week volatility (CV = std / mean)
    def rolling_cv(x):
        m = x.rolling(8, min_periods=2).mean()
        s = x.rolling(8, min_periods=2).std()
        return s / m.replace(0, np.nan)

    weekly["volatility_cv"] = weekly.groupby(["Store", "Dept"])["Weekly_Sales"].transform(rolling_cv)

    # Risk components — clip extreme values so one outlier dept can't dominate
    weekly["trend_decline_risk"] = weekly["trend_8w_pct"].apply(
        lambda x: min(max(0.0, -x), 3.0) if pd.notna(x) and np.isfinite(x) else 0.0
    )
    weekly["volatility_risk"] = weekly["volatility_cv"].apply(
        lambda x: min(1.0, x) if pd.notna(x) and np.isfinite(x) else 0.0
    )
    weekly["wow_decline_risk"] = weekly["wow_change_pct"].apply(
        lambda x: min(max(0.0, -x), 3.0) if pd.notna(x) and np.isfinite(x) else 0.0
    )

    weekly["risk_score"] = (
        50 * weekly["trend_decline_risk"]
        + 30 * weekly["volatility_risk"]
        + 20 * weekly["wow_decline_risk"]
    )

    return weekly


df_raw   = load_data()
scored_all = build_risk_scores(df_raw)


# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚠️ Filters")

    store_types = sorted(df_raw["Type"].dropna().unique())
    selected_types = st.multiselect(
        "Store Type", store_types, default=store_types,
    )

    tier_options = ["High", "Medium", "Low"]
    selected_tiers = st.multiselect(
        "Risk Tier", tier_options, default=tier_options,
    )

    all_depts = sorted(df_raw["Dept"].unique())
    selected_depts = st.multiselect(
        "Departments (leave blank = all)", all_depts, default=[],
    )

    top_n = st.slider("Rows in rankings table", 5, 30, 15)

    st.markdown("---")
    st.caption("Risk score = 50×trend + 30×volatility + 20×WoW decline")
    st.caption(f"High ≥ {RISK_HIGH_THRESHOLD} | Medium ≥ {RISK_MED_THRESHOLD} | Low < {RISK_MED_THRESHOLD}")
    
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


# ── Latest-week scored slice ──────────────────────────────────────────────────
latest_week = scored_all["week_start"].max()

scored = (
    scored_all[scored_all["week_start"] == latest_week]
    .merge(df_raw[["Store", "Type", "Size"]].drop_duplicates(), on="Store", how="left")
    .copy()
)

# Apply sidebar filters
if selected_types:
    scored = scored[scored["Type"].isin(selected_types)]
if selected_depts:
    scored = scored[scored["Dept"].isin(selected_depts)]

scored["risk_tier"] = scored["risk_score"].apply(risk_tier)

if selected_tiers:
    scored = scored[scored["risk_tier"].isin(selected_tiers)]

scored["risk_rank"] = scored["risk_score"].rank(ascending=False, method="min").astype(int)
scored = scored.sort_values("risk_score", ascending=False)

# One row per store — highest-risk dept per store (mirrors QUALIFY logic in SQL)
scored_per_store = scored.drop_duplicates("Store")

# Full 8-week history for sparklines / trend chart
history_8w = (
    scored_all[
        scored_all["week_start"] >= scored_all["week_start"].max()
        - pd.Timedelta(weeks=8)
    ]
    .merge(df_raw[["Store", "Type"]].drop_duplicates(), on="Store", how="left")
    .copy()
)
if selected_types:
    history_8w = history_8w[history_8w["Type"].isin(selected_types)]


# ── KPI Summary ───────────────────────────────────────────────────────────────
highest_score  = scored_per_store["risk_score"].max() if not scored_per_store.empty else 0
highest_store  = int(scored_per_store.iloc[0]["Store"]) if not scored_per_store.empty else "—"
highest_dept   = int(scored_per_store.iloc[0]["Dept"])  if not scored_per_store.empty else "—"

n_high   = (scored_per_store["risk_tier"] == "High").sum()
n_medium = (scored_per_store["risk_tier"] == "Medium").sum()
n_low    = (scored_per_store["risk_tier"] == "Low").sum()

avg_cv   = scored["volatility_cv"].replace([np.inf, -np.inf], np.nan).mean()
avg_wow  = scored["wow_change_pct"].replace([np.inf, -np.inf], np.nan).mean()


# ── Header Banner ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="top-banner">
  <h2>⚠️ Walmart Weekly Sales — At-Risk Stores</h2>
  <span>Scored week of {latest_week.strftime('%b %d, %Y')} &nbsp;|&nbsp;
  Weights: Trend 50% · Volatility 30% · WoW 20%</span>
</div>
""", unsafe_allow_html=True)


# ── KPI Tiles ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Highest Risk Score</div>
      <div class="kpi-value" style="color:{RED}">{highest_score:.1f}</div>
      <div class="kpi-sub">Store {highest_store} / Dept {highest_dept}</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">High Risk Stores</div>
      <div class="kpi-value" style="color:{RED}">{n_high}</div>
      <div class="kpi-sub">Score ≥ {RISK_HIGH_THRESHOLD}</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Medium Risk Stores</div>
      <div class="kpi-value" style="color:{AMBER}">{n_medium}</div>
      <div class="kpi-sub">Score {RISK_MED_THRESHOLD}–{RISK_HIGH_THRESHOLD}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    cv_color = RED if pd.notna(avg_cv) and avg_cv > 0.25 else (AMBER if pd.notna(avg_cv) and avg_cv > 0.15 else GREEN)
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Avg Volatility (CV)</div>
      <div class="kpi-value" style="color:{cv_color}">{avg_cv:.2f}</div>
      <div class="kpi-sub">8W rolling fleet avg</div>
    </div>""", unsafe_allow_html=True)

with k5:
    wow_color = RED if pd.notna(avg_wow) and avg_wow < 0 else GREEN
    wow_arrow = "▼" if pd.notna(avg_wow) and avg_wow < 0 else "▲"
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Avg WoW Change</div>
      <div class="kpi-value" style="color:{wow_color}">
        {avg_wow*100:+.1f}%
      </div>
      <div class="kpi-sub">{wow_arrow} Fleet avg this week</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 2: Rankings Table + Risk Tier Histogram ───────────────────────────────
col_tbl, col_hist = st.columns([1.5, 1])

with col_tbl:
    st.markdown('<div class="chart-title">At-Risk Rankings — Store / Department</div>', unsafe_allow_html=True)

    display = scored.head(top_n)[
        ["risk_rank", "Store", "Type", "Dept", "risk_score", "risk_tier",
         "volatility_cv", "wow_change_pct", "trend_8w_pct", "Weekly_Sales"]
    ].copy()

    def fmt_pct(v):
        if pd.isna(v) or not np.isfinite(v):
            return "—"
        return f"{v*100:+.1f}%"

    rank_col   = display["risk_rank"].tolist()
    store_col  = [f"Store {int(s)}" for s in display["Store"]]
    type_col   = display["Type"].tolist()
    dept_col   = [str(int(d)) for d in display["Dept"]]
    score_col  = [f"{v:.1f}" for v in display["risk_score"]]
    tier_col   = display["risk_tier"].tolist()
    cv_col     = [f"{v:.2f}" if pd.notna(v) and np.isfinite(v) else "—" for v in display["volatility_cv"]]
    wow_col    = [fmt_pct(v) for v in display["wow_change_pct"]]
    trend_col  = [fmt_pct(v) for v in display["trend_8w_pct"]]
    sales_col  = [f"${v/1e3:.0f}K" for v in display["Weekly_Sales"]]

    score_bg = [tier_bg(t) for t in tier_col]
    score_fc = [tier_color(t) for t in tier_col]

    def pct_color(vals, invert=False):
        out = []
        for v in display[vals]:
            if pd.isna(v) or not np.isfinite(v):
                out.append("#5F6368")
            elif v < 0:
                out.append(RED if not invert else GREEN)
            else:
                out.append(GREEN if not invert else RED)
        return out

    fig_tbl = go.Figure(data=[go.Table(
        columnwidth=[28, 65, 38, 38, 58, 52, 52, 65, 65, 60],
        header=dict(
            values=["#", "Store", "Type", "Dept", "Risk Score", "Tier",
                    "Volatility CV", "WoW Chg", "8W Trend", "Sales"],
            fill_color=DARK_BLUE,
            font=dict(color="white", size=11),
            align=["center","left","center","center","right","center","right","right","right","right"],
            height=30,
        ),
        cells=dict(
            values=[rank_col, store_col, type_col, dept_col,
                    score_col, tier_col, cv_col, wow_col, trend_col, sales_col],
            fill_color=[
                ["#F8F9FA"] * len(rank_col),
                ["white"]   * len(store_col),
                ["white"]   * len(type_col),
                ["white"]   * len(dept_col),
                score_bg,
                score_bg,
                ["white"]   * len(cv_col),
                ["#FCE8E6" if pd.notna(v) and np.isfinite(v) and v < 0
                 else ("#E6F4EA" if pd.notna(v) and np.isfinite(v) and v >= 0 else "white")
                 for v in display["wow_change_pct"]],
                ["#FCE8E6" if pd.notna(v) and np.isfinite(v) and v < 0
                 else ("#E6F4EA" if pd.notna(v) and np.isfinite(v) and v >= 0 else "white")
                 for v in display["trend_8w_pct"]],
                ["white"] * len(sales_col),
            ],
            font=dict(
                color=[
                    ["#5F6368"] * len(rank_col),
                    ["#202124"] * len(store_col),
                    ["#5F6368"] * len(type_col),
                    ["#5F6368"] * len(dept_col),
                    score_fc,
                    score_fc,
                    ["#202124"] * len(cv_col),
                    pct_color("wow_change_pct"),
                    pct_color("trend_8w_pct"),
                    ["#202124"] * len(sales_col),
                ],
                size=11,
            ),
            align=["center","left","center","center","right","center","right","right","right","right"],
            height=26,
        ),
    )])
    fig_tbl.update_layout(
        height=min(60 + top_n * 26, 620),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_tbl, use_container_width=True)

with col_hist:
    st.markdown('<div class="chart-title">Stores by Risk Tier</div>', unsafe_allow_html=True)

    tier_counts = (
        scored_per_store["risk_tier"]
        .value_counts()
        .reindex(["High", "Medium", "Low"], fill_value=0)
        .reset_index()
    )
    tier_counts.columns = ["tier", "count"]
    tier_counts["color"] = tier_counts["tier"].map({"High": RED, "Medium": AMBER, "Low": GREEN})

    fig_hist = go.Figure(go.Bar(
        y=tier_counts["tier"],
        x=tier_counts["count"],
        orientation="h",
        marker_color=tier_counts["color"],
        text=tier_counts["count"],
        textposition="outside",
        hovertemplate="%{y}: %{x} stores<extra></extra>",
    ))
    fig_hist.update_layout(
        height=160,
        margin=dict(l=0, r=40, t=4, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=12)),
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Risk score distribution
    st.markdown('<div class="chart-title" style="margin-top:12px">Risk Score Distribution</div>', unsafe_allow_html=True)

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(
        x=scored_per_store["risk_score"],
        nbinsx=20,
        marker_color=BLUE,
        opacity=0.75,
        hovertemplate="Score %{x:.0f}–%{x:.0f}<br>Count: %{y}<extra></extra>",
    ))
    fig_dist.add_vline(x=RISK_MED_THRESHOLD,  line_dash="dot", line_color=AMBER,
                       annotation_text="Med",  annotation_font_size=9)
    fig_dist.add_vline(x=RISK_HIGH_THRESHOLD, line_dash="dot", line_color=RED,
                       annotation_text="High", annotation_font_size=9)
    fig_dist.update_layout(
        height=160,
        margin=dict(l=0, r=0, t=4, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(size=9), title="Risk Score"),
        yaxis=dict(showgrid=True, gridcolor=BORDER, tickfont=dict(size=9), title="# Stores"),
        showlegend=False,
        bargap=0.05,
    )
    st.plotly_chart(fig_dist, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 3: Scatter plot + Risk component breakdown ────────────────────────────
col_scatter, col_breakdown = st.columns([1.2, 0.8])

with col_scatter:
    st.markdown('<div class="chart-title">Volatility vs 8W Trend — Scatter (bubble size = weekly revenue at risk)</div>', unsafe_allow_html=True)

    scatter_data = scored_per_store.dropna(subset=["volatility_cv", "trend_8w_pct"]).copy()
    scatter_data = scatter_data[
        np.isfinite(scatter_data["volatility_cv"]) &
        np.isfinite(scatter_data["trend_8w_pct"])
    ]
    scatter_data["tier_color"] = scatter_data["risk_tier"].map(
        {"High": RED, "Medium": AMBER, "Low": GREEN}
    )

    fig_sc = go.Figure()

    # Shaded high-risk quadrant (high CV + negative trend)
    cv_avg = scatter_data["volatility_cv"].median()
    fig_sc.add_shape(
        type="rect",
        x0=cv_avg, x1=scatter_data["volatility_cv"].max() * 1.1,
        y0=scatter_data["trend_8w_pct"].min() * 1.1, y1=0,
        fillcolor="rgba(197,34,31,0.05)",
        line_width=0,
    )
    fig_sc.add_annotation(
        x=scatter_data["volatility_cv"].max() * 0.95,
        y=scatter_data["trend_8w_pct"].min() * 0.9,
        text="High risk zone",
        showarrow=False,
        font=dict(size=10, color=RED),
    )

    for tier in ["High", "Medium", "Low"]:
        sub = scatter_data[scatter_data["risk_tier"] == tier]
        if sub.empty:
            continue
        fig_sc.add_trace(go.Scatter(
            x=sub["volatility_cv"],
            y=sub["trend_8w_pct"] * 100,
            mode="markers+text",
            name=tier,
            marker=dict(
                size=np.sqrt(sub["Weekly_Sales"] / 1000).clip(6, 28),
                color=tier_color(tier),
                opacity=0.75,
                line=dict(color="white", width=1),
            ),
            text=[f"S{int(s)}" for s in sub["Store"]],
            textposition="top center",
            textfont=dict(size=8),
            customdata=sub[["Store", "Dept", "risk_score", "Weekly_Sales"]].values,
            hovertemplate=(
                "<b>Store %{customdata[0]} / Dept %{customdata[1]}</b><br>"
                "Risk Score: %{customdata[2]:.1f}<br>"
                "Volatility CV: %{x:.2f}<br>"
                "8W Trend: %{y:.1f}%<br>"
                "Weekly Sales: $%{customdata[3]:,.0f}<extra></extra>"
            ),
        ))

    fig_sc.add_hline(y=0,    line_dash="dot", line_color=BORDER, line_width=1)
    fig_sc.add_vline(x=cv_avg, line_dash="dot", line_color=BORDER, line_width=1,
                     annotation_text=f"Median CV {cv_avg:.2f}",
                     annotation_font_size=9)

    fig_sc.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            title="Risk Tier", orientation="v",
            font=dict(size=11),
        ),
        xaxis=dict(
            title="Volatility CV (8W rolling)",
            showgrid=True, gridcolor=BORDER, tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="8W Trend Change %",
            showgrid=True, gridcolor=BORDER, ticksuffix="%", tickfont=dict(size=10),
        ),
        hovermode="closest",
    )
    st.plotly_chart(fig_sc, use_container_width=True)

with col_breakdown:
    st.markdown('<div class="chart-title">Risk Score Components — Top 10 Stores</div>', unsafe_allow_html=True)

    top10 = scored_per_store.head(10).copy()
    top10["store_label"] = [f"Store {int(s)}" for s in top10["Store"]]
    top10 = top10.sort_values("risk_score")

    comp_trend = (50 * top10["trend_decline_risk"]).clip(lower=0)
    comp_vol   = (30 * top10["volatility_risk"]).clip(lower=0)
    comp_wow   = (20 * top10["wow_decline_risk"]).clip(lower=0)

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        name="Trend decline (50%)",
        y=top10["store_label"],
        x=comp_trend,
        orientation="h",
        marker_color=RED,
        hovertemplate="%{y}<br>Trend component: %{x:.1f}<extra></extra>",
    ))
    fig_comp.add_trace(go.Bar(
        name="Volatility (30%)",
        y=top10["store_label"],
        x=comp_vol,
        orientation="h",
        marker_color=AMBER,
        hovertemplate="%{y}<br>Volatility component: %{x:.1f}<extra></extra>",
    ))
    fig_comp.add_trace(go.Bar(
        name="WoW decline (20%)",
        y=top10["store_label"],
        x=comp_wow,
        orientation="h",
        marker_color=RED_LIGHT,
        hovertemplate="%{y}<br>WoW component: %{x:.1f}<extra></extra>",
    ))
    fig_comp.update_layout(
        barmode="stack",
        height=360,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=10),
        ),
        xaxis=dict(
            title="Risk Score",
            showgrid=True, gridcolor=BORDER, tickfont=dict(size=9),
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 4: 8-Week trend for top at-risk stores ────────────────────────────────
st.markdown('<div class="chart-title">8-Week Sales Trend — At-Risk Stores</div>', unsafe_allow_html=True)

default_risk_stores = scored_per_store.head(5)["Store"].astype(int).tolist()
all_stores = sorted(df_raw["Store"].unique())

trend_stores = st.multiselect(
    "Stores to plot (default = top 5 highest risk)",
    options=all_stores,
    default=default_risk_stores,
    format_func=lambda x: f"Store {x}",
)

if trend_stores:
    trend_data = (
        history_8w[history_8w["Store"].isin(trend_stores)]
        .groupby(["week_start", "Store"])["Weekly_Sales"]
        .sum()
        .reset_index()
        .sort_values(["Store", "week_start"])
    )

    palette = [RED, AMBER, RED_LIGHT, "#9C27B0", BLUE, GREEN, "#FF5722", "#607D8B"]

    fig_trend = go.Figure()
    for i, store_id in enumerate(trend_stores):
        sd = trend_data[trend_data["Store"] == store_id]
        store_tier = scored_per_store.loc[
            scored_per_store["Store"] == store_id, "risk_tier"
        ].values
        tier_label = f" [{store_tier[0]}]" if len(store_tier) > 0 else ""
        fig_trend.add_trace(go.Scatter(
            x=sd["week_start"],
            y=sd["Weekly_Sales"],
            name=f"Store {store_id}{tier_label}",
            mode="lines+markers",
            line=dict(color=palette[i % len(palette)], width=2),
            marker=dict(size=5),
            hovertemplate=(
                f"Store {store_id}<br>"
                "%{x|%b %d %Y}<br>"
                "Sales: $%{y:,.0f}<extra></extra>"
            ),
        ))

    fig_trend.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=11),
        ),
        xaxis=dict(showgrid=False, tickfont=dict(size=10), linecolor=BORDER),
        yaxis=dict(
            showgrid=True, gridcolor=BORDER,
            tickformat="$,.0f", tickfont=dict(size=10),
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Select at least one store above to show its trend.")
