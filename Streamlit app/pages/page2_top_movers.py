"""
Walmart Weekly Sales — Page 2: Top Movers
==========================================
Run:
    streamlit run page2_top_movers.py

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
DATA_DIR    = os.path.dirname(__file__)
SALES_FILE  = os.path.join(DATA_DIR, "raw_sales.csv")
STORES_FILE = os.path.join(DATA_DIR, "raw_stores.csv")

BLUE       = "#1A73E8"
DARK_BLUE  = "#0D47A1"
AMBER      = "#E37400"
GREEN      = "#137333"
GREEN_LIGHT= "#34A853"
RED        = "#C5221F"
RED_LIGHT  = "#E57368"
BORDER     = "#DADCE0"

st.set_page_config(
    page_title="Walmart Top Movers",
    page_icon="📈",
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
    .kpi-value { font-size: 26px; font-weight: 500; color: #202124; line-height: 1; }
    .kpi-delta-pos { font-size: 12px; color: #137333; margin-top: 5px; }
    .kpi-delta-neg { font-size: 12px; color: #C5221F; margin-top: 5px; }
    .kpi-delta-neu { font-size: 12px; color: #5F6368; margin-top: 5px; }

    .chart-title {
        font-size: 11px;
        font-weight: 500;
        color: #5F6368;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .section-title {
        font-size: 13px;
        font-weight: 500;
        color: #202124;
        margin: 4px 0 10px 0;
    }
    hr { border-top: 1px solid #DADCE0; margin: 8px 0 16px 0; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }

    /* Rank badge in table */
    .rank-badge {
        display: inline-block;
        width: 22px; height: 22px;
        line-height: 22px;
        text-align: center;
        border-radius: 50%;
        background: #E8F0FE;
        color: #1A73E8;
        font-size: 11px;
        font-weight: 500;
    }
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
        sales["IsHoliday"].astype(str).str.upper().map({"TRUE": True, "FALSE": False})
    )
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
    )

    all_stores = sorted(df_raw["Store"].unique())
    selected_stores = st.multiselect(
        "Stores (leave blank = all)", all_stores, default=[],
        help="Narrow to specific store IDs",
    )

    min_date = df_raw["week_start"].min().date()
    max_date = df_raw["week_start"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    top_n = st.slider("Top N stores to show", min_value=3, max_value=15, value=5)

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
if selected_stores:
    df = df[df["Store"].isin(selected_stores)]
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    s, e = date_range
    df = df[(df["week_start"].dt.date >= s) & (df["week_start"].dt.date <= e)]


# ── Core Aggregations ─────────────────────────────────────────────────────────

# 1. Weekly sales by store  (02_overview_top_movers logic)
by_store = (
    df.groupby(["week_start", "Store", "Type"])["Weekly_Sales"]
    .sum()
    .reset_index()
    .sort_values(["Store", "week_start"])
)
by_store["delta_sales"] = by_store.groupby("Store")["Weekly_Sales"].diff()
by_store["delta_pct"]   = by_store.groupby("Store")["Weekly_Sales"].pct_change()

# Latest week slice
latest_week = by_store["week_start"].max()
prev_week   = by_store[by_store["week_start"] < latest_week]["week_start"].max()

latest_slice = by_store[by_store["week_start"] == latest_week].copy()
latest_slice["rank"] = latest_slice["Weekly_Sales"].rank(ascending=False).astype(int)
latest_slice = latest_slice.sort_values("rank")

# 2. Dept contribution  (vw_dept_contribution logic)
dept_week  = df.groupby(["week_start", "Dept"])["Weekly_Sales"].sum().reset_index()
total_week = (
    df.groupby("week_start")["Weekly_Sales"]
    .sum()
    .reset_index()
    .rename(columns={"Weekly_Sales": "total_sales"})
)
dept_contrib = dept_week.merge(total_week, on="week_start")
dept_contrib["dept_share"] = dept_contrib["Weekly_Sales"] / dept_contrib["total_sales"]
dept_contrib = dept_contrib.sort_values(["Dept", "week_start"])
dept_contrib["prev_sales"] = dept_contrib.groupby("Dept")["Weekly_Sales"].shift(1)
dept_contrib["wow_pct"]    = (
    (dept_contrib["Weekly_Sales"] - dept_contrib["prev_sales"])
    / dept_contrib["prev_sales"]
)

# Latest week dept slice (for treemap)
dept_latest = dept_contrib[dept_contrib["week_start"] == latest_week].copy()
dept_latest = dept_latest[dept_latest["Weekly_Sales"] > 0]

# All-time dept totals for overall share
dept_totals = (
    df.groupby("Dept")["Weekly_Sales"]
    .sum()
    .reset_index()
    .rename(columns={"Weekly_Sales": "total_dept_sales"})
)
grand_total = dept_totals["total_dept_sales"].sum()
dept_totals["share_pct"] = dept_totals["total_dept_sales"] / grand_total * 100

# 3. Summary KPIs
total_latest  = latest_slice["Weekly_Sales"].sum()
total_prev    = by_store[by_store["week_start"] == prev_week]["Weekly_Sales"].sum()
wow_fleet     = (total_latest - total_prev) / total_prev if total_prev else 0

gainers  = latest_slice[latest_slice["delta_sales"] > 0]
decliners= latest_slice[latest_slice["delta_sales"] < 0]
n_gainers  = len(gainers)
n_decliners= len(decliners)

biggest_gain = gainers.nlargest(1, "delta_sales")
biggest_drop = decliners.nsmallest(1, "delta_sales")


# ── Header Banner ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="top-banner">
  <h2>📈 Walmart Weekly Sales — Top Movers</h2>
  <span>Week of {latest_week.strftime('%b %d, %Y')} &nbsp;|&nbsp; vs {prev_week.strftime('%b %d, %Y')}</span>
</div>
""", unsafe_allow_html=True)


# ── KPI Tiles ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    css = "pos" if wow_fleet >= 0 else "neg"
    arrow = "▲" if wow_fleet >= 0 else "▼"
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Fleet-Wide WoW Change</div>
      <div class="kpi-value kpi-delta-{css}">{wow_fleet*100:+.1f}%</div>
      <div class="kpi-delta-neu">${total_latest/1e6:.1f}M this week vs ${total_prev/1e6:.1f}M</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Stores Gaining</div>
      <div class="kpi-value kpi-delta-pos">{n_gainers}</div>
      <div class="kpi-delta-pos">▲ WoW positive delta</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-block">
      <div class="kpi-label">Stores Declining</div>
      <div class="kpi-value kpi-delta-neg">{n_decliners}</div>
      <div class="kpi-delta-neg">▼ WoW negative delta</div>
    </div>""", unsafe_allow_html=True)

with k4:
    if not biggest_gain.empty and not biggest_drop.empty:
        g_store = int(biggest_gain.iloc[0]["Store"])
        g_val   = biggest_gain.iloc[0]["delta_sales"]
        d_store = int(biggest_drop.iloc[0]["Store"])
        d_val   = biggest_drop.iloc[0]["delta_sales"]
        st.markdown(f"""
        <div class="kpi-block">
          <div class="kpi-label">Biggest Swing This Week</div>
          <div class="kpi-value" style="font-size:16px; color:#202124;">
            Store {g_store} <span style="color:#137333">{g_val/1e3:+.0f}K</span> &nbsp;|&nbsp;
            Store {d_store} <span style="color:#C5221F">{d_val/1e3:+.0f}K</span>
          </div>
          <div class="kpi-delta-neu">Top gainer vs top decliner</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 2: Rankings Table + Gainers/Decliners ────────────────────────────────
col_table, col_bars = st.columns([1.2, 0.8])

with col_table:
    st.markdown('<div class="chart-title">Store Rankings — WoW Sales Delta</div>', unsafe_allow_html=True)

    display = latest_slice[["rank", "Store", "Type", "Weekly_Sales", "delta_sales", "delta_pct"]].copy()
    display = display.sort_values("rank").head(20)
    display["Store"] = display["Store"].astype(int)

    # Build Plotly table
    rank_col    = display["rank"].tolist()
    store_col   = [f"Store {s}" for s in display["Store"]]
    type_col    = display["Type"].tolist()
    sales_col   = [f"${v/1e6:.2f}M" for v in display["Weekly_Sales"]]
    delta_col   = [f"{v/1e3:+.0f}K" if pd.notna(v) else "—" for v in display["delta_sales"]]
    pct_col     = [f"{v*100:+.1f}%" if pd.notna(v) else "—" for v in display["delta_pct"]]

    delta_colors = [
        GREEN if pd.notna(v) and v > 0 else (RED if pd.notna(v) and v < 0 else "#5F6368")
        for v in display["delta_sales"]
    ]

    fig_table = go.Figure(data=[go.Table(
        columnwidth=[30, 70, 40, 80, 70, 60],
        header=dict(
            values=["#", "Store", "Type", "Total Sales", "WoW Delta ($)", "WoW Delta (%)"],
            fill_color=DARK_BLUE,
            font=dict(color="white", size=11),
            align=["center", "left", "center", "right", "right", "right"],
            height=30,
        ),
        cells=dict(
            values=[rank_col, store_col, type_col, sales_col, delta_col, pct_col],
            fill_color=[
                ["#F8F9FA"] * len(rank_col),
                ["white"] * len(store_col),
                ["white"] * len(type_col),
                ["white"] * len(sales_col),
                [
                    "#E6F4EA" if pd.notna(v) and v > 0
                    else ("#FCE8E6" if pd.notna(v) and v < 0 else "white")
                    for v in display["delta_sales"]
                ],
                [
                    "#E6F4EA" if pd.notna(v) and v > 0
                    else ("#FCE8E6" if pd.notna(v) and v < 0 else "white")
                    for v in display["delta_pct"]
                ],
            ],
            font=dict(
                color=[
                    ["#5F6368"] * len(rank_col),
                    ["#202124"] * len(store_col),
                    ["#5F6368"] * len(type_col),
                    ["#202124"] * len(sales_col),
                    delta_colors,
                    delta_colors,
                ],
                size=11,
            ),
            align=["center", "left", "center", "right", "right", "right"],
            height=26,
        ),
    )])
    fig_table.update_layout(
        height=min(60 + len(display) * 26, 560),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_table, use_container_width=True)

with col_bars:
    top_gainers   = gainers.nlargest(top_n, "delta_sales")
    top_decliners = decliners.nsmallest(top_n, "delta_sales")

    # Gainers chart
    st.markdown('<div class="chart-title">Top Gainers This Week</div>', unsafe_allow_html=True)
    if not top_gainers.empty:
        fig_gain = go.Figure(go.Bar(
            x=top_gainers["delta_sales"],
            y=[f"Store {int(s)}" for s in top_gainers["Store"]],
            orientation="h",
            marker_color=GREEN,
            text=[f"+${v/1e3:.0f}K" for v in top_gainers["delta_sales"]],
            textposition="outside",
            hovertemplate="Store %{y}<br>Delta: $%{x:,.0f}<extra></extra>",
        ))
        fig_gain.update_layout(
            height=200,
            margin=dict(l=0, r=60, t=4, b=0),
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor=BORDER, tickformat="$,.0f", tickfont=dict(size=9)),
            yaxis=dict(showgrid=False, tickfont=dict(size=11), autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(fig_gain, use_container_width=True)
    else:
        st.info("No gaining stores in the selected period.")

    # Decliners chart
    st.markdown('<div class="chart-title">Top Decliners This Week</div>', unsafe_allow_html=True)
    if not top_decliners.empty:
        fig_drop = go.Figure(go.Bar(
            x=top_decliners["delta_sales"],
            y=[f"Store {int(s)}" for s in top_decliners["Store"]],
            orientation="h",
            marker_color=RED,
            text=[f"${v/1e3:.0f}K" for v in top_decliners["delta_sales"]],
            textposition="outside",
            hovertemplate="Store %{y}<br>Delta: $%{x:,.0f}<extra></extra>",
        ))
        fig_drop.update_layout(
            height=200,
            margin=dict(l=0, r=60, t=4, b=0),
            plot_bgcolor="white", paper_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor=BORDER, tickformat="$,.0f", tickfont=dict(size=9)),
            yaxis=dict(showgrid=False, tickfont=dict(size=11), autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(fig_drop, use_container_width=True)
    else:
        st.info("No declining stores in the selected period.")

st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 3: Treemap + WoW Dept Bar ─────────────────────────────────────────────
col_tree, col_dept = st.columns([1.1, 0.9])

with col_tree:
    st.markdown('<div class="chart-title">Department Sales Contribution — Treemap (size = revenue, color = WoW change %)</div>', unsafe_allow_html=True)

    treemap_data = dept_latest.merge(
        dept_totals[["Dept", "total_dept_sales"]], on="Dept", how="left"
    ).dropna(subset=["wow_pct"])

    # Cap extreme WoW values for color scale readability
    treemap_data["wow_pct_capped"] = treemap_data["wow_pct"].clip(-0.5, 0.5)

    fig_tree = px.treemap(
        treemap_data,
        path=["Dept"],
        values="Weekly_Sales",
        color="wow_pct_capped",
        color_continuous_scale=[
            [0.0, RED],
            [0.4, "#FADDD9"],
            [0.5, "#F8F9FA"],
            [0.6, "#CEEAD6"],
            [1.0, GREEN],
        ],
        color_continuous_midpoint=0,
        hover_data={"wow_pct": ":.1%", "dept_share": ":.1%"},
        custom_data=["Dept", "wow_pct", "dept_share"],
    )
    fig_tree.update_traces(
        hovertemplate="<b>Dept %{customdata[0]}</b><br>"
                      "Sales: $%{value:,.0f}<br>"
                      "WoW: %{customdata[1]:.1%}<br>"
                      "Share: %{customdata[2]:.1%}<extra></extra>",
        textfont=dict(size=11),
    )
    fig_tree.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=4, b=0),
        coloraxis_colorbar=dict(
            title="WoW %",
            tickformat=".0%",
            thickness=12,
            len=0.8,
        ),
    )
    st.plotly_chart(fig_tree, use_container_width=True)

with col_dept:
    st.markdown('<div class="chart-title">WoW Sales Change — Top &amp; Bottom Departments</div>', unsafe_allow_html=True)

    dept_wow = dept_latest.dropna(subset=["wow_pct"]).copy()
    dept_wow = dept_wow[dept_wow["Weekly_Sales"] > 1000]  # filter noise

    top_gain_dept = dept_wow.nlargest(5, "wow_pct")
    top_drop_dept = dept_wow.nsmallest(5, "wow_pct")
    combined      = pd.concat([top_gain_dept, top_drop_dept]).drop_duplicates("Dept")
    combined      = combined.sort_values("wow_pct")

    bar_colors = [GREEN if v >= 0 else RED for v in combined["wow_pct"]]

    fig_dept = go.Figure(go.Bar(
        x=combined["wow_pct"] * 100,
        y=[f"Dept {int(d)}" for d in combined["Dept"]],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v*100:+.1f}%" for v in combined["wow_pct"]],
        textposition="outside",
        hovertemplate="Dept %{y}<br>WoW: %{x:.1f}%<extra></extra>",
    ))
    fig_dept.add_vline(x=0, line_width=1.5, line_color=BORDER)
    fig_dept.update_layout(
        height=340,
        margin=dict(l=0, r=55, t=4, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            showgrid=True, gridcolor=BORDER,
            ticksuffix="%", tickfont=dict(size=9),
            zeroline=False,
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig_dept, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Row 4: Store-level weekly trend (multi-line) ──────────────────────────────
st.markdown('<div class="chart-title">Weekly Sales Trend — Selected Stores Over Time</div>', unsafe_allow_html=True)

# Default to top 5 stores by total sales
top5_stores = (
    df.groupby("Store")["Weekly_Sales"]
    .sum()
    .nlargest(5)
    .index.tolist()
)
trend_stores = st.multiselect(
    "Stores to plot", all_stores,
    default=top5_stores,
    format_func=lambda x: f"Store {x}",
)

if trend_stores:
    trend_data = by_store[by_store["Store"].isin(trend_stores)]

    fig_trend = go.Figure()
    palette = [BLUE, GREEN, AMBER, RED, "#9C27B0", "#00BCD4", "#FF5722", "#607D8B"]

    for i, store_id in enumerate(trend_stores):
        sd = trend_data[trend_data["Store"] == store_id].sort_values("week_start")
        fig_trend.add_trace(go.Scatter(
            x=sd["week_start"],
            y=sd["Weekly_Sales"],
            name=f"Store {store_id}",
            line=dict(color=palette[i % len(palette)], width=2),
            hovertemplate=f"Store {store_id}<br>%{{x|%b %d %Y}}<br>${{y:,.0f}}<extra></extra>",
        ))

    fig_trend.update_layout(
        height=280,
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
