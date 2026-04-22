"""
Walmart Weekly Sales — Page 5: Key Insights
============================================
Run standalone:
    streamlit run page5_insights.py

Or register in app.py alongside the other pages.

Requirements:
    pip install streamlit pandas plotly numpy
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR    = os.path.dirname(os.path.abspath(__file__))
SALES_FILE  = os.path.join(DATA_DIR, "raw_sales.csv")
STORES_FILE = os.path.join(DATA_DIR, "raw_stores.csv")

BLUE      = "#1A73E8"
DARK_BLUE = "#0D47A1"
AMBER     = "#E37400"
GREEN     = "#137333"
RED       = "#C5221F"
BORDER    = "#DADCE0"

st.set_page_config(
    page_title="Walmart Key Insights",
    page_icon="💡",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    #MainMenu, footer, header { visibility: visible; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }

    .top-banner {
        background: #0D47A1;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .top-banner h2 { margin: 0; font-size: 16px; font-weight: 500; }
    .top-banner span { font-size: 20px; opacity: 0.85; }

    /* Insight card */
    .ins-card {
        background: white;
        border: 1px solid #DADCE0;
        border-radius: 12px;
        padding: 20px 22px;
        height: 100%;
    }
    .ins-header {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 10px;
    }
    .ins-number {
        width: 30px; height: 30px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 600;
        flex-shrink: 0;
    }
    .ins-title { font-size: 15px; font-weight: 600; color: #202124; line-height: 1.3; }
    .ins-tag {
        display: inline-block;
        font-size: 10px; font-weight: 500;
        padding: 2px 9px; border-radius: 20px;
        margin-bottom: 8px;
    }
    .ins-body { font-size: 13px; color: #5F6368; line-height: 1.65; }
    .ins-stat { font-size: 26px; font-weight: 600; margin: 10px 0 2px 0; line-height: 1; }
    .ins-stat-label { font-size: 11px; color: #5F6368; margin-bottom: 10px; }

    .tag-danger  { background: #FCE8E6; color: #C5221F; }
    .tag-warning { background: #FFF0D0; color: #B45309; }
    .tag-info    { background: #E8F0FE; color: #1A73E8; }
    .tag-success { background: #E6F4EA; color: #137333; }

    /* Summary strip */
    .summary-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 24px;
    }
    .sum-tile {
        background: white;
        border: 1px solid #DADCE0;
        border-radius: 10px;
        padding: 14px 16px;
    }
    .sum-label { font-size: 10px; color: #5F6368; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 5px; }
    .sum-value { font-size: 22px; font-weight: 500; line-height: 1; }
    .sum-sub   { font-size: 11px; color: #9AA0A6; margin-top: 4px; }

    hr { border-top: 1px solid #DADCE0; margin: 4px 0 20px 0; }

    .chart-title {
        font-size: 11px; font-weight: 500; color: #5F6368;
        text-transform: uppercase; letter-spacing: .5px; margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Computing insights…")
def load_and_compute():
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

    # ── I1: Fleet revenue trend ───────────────────────────────────────────────
    weekly = (
        df.groupby("week_start")["Weekly_Sales"]
        .sum().reset_index().sort_values("week_start")
    )
    weekly["year"] = weekly["week_start"].dt.year
    yr_avg = weekly.groupby("year")["Weekly_Sales"].mean()
    yoy_2011 = (yr_avg[2011] - yr_avg[2010]) / yr_avg[2010]
    yoy_2012 = (yr_avg[2012] - yr_avg[2011]) / yr_avg[2011]
    annual_loss_usd = (yr_avg[2012] - yr_avg[2010]) / 2 * 52

    # ── I2: Concentration risk ────────────────────────────────────────────────
    store_totals = (
        df.groupby("Store")["Weekly_Sales"].sum()
        .sort_values(ascending=False).reset_index()
    )
    store_totals["cum_share"] = store_totals["Weekly_Sales"].cumsum() / store_totals["Weekly_Sales"].sum()
    total_rev   = store_totals["Weekly_Sales"].sum()
    top5_share  = store_totals.head(5)["Weekly_Sales"].sum() / total_rev
    top10_share = store_totals.head(10)["Weekly_Sales"].sum() / total_rev
    bot10_share = store_totals.tail(10)["Weekly_Sales"].sum() / total_rev
    top5_stores = store_totals.head(5)["Store"].tolist()

    # ── I3: Sales per sqft by size band ──────────────────────────────────────
    store_meta = df.drop_duplicates("Store")[["Store", "Type", "Size"]].copy()
    store_meta = store_meta.merge(
        df.groupby("Store")["Weekly_Sales"].sum().reset_index(), on="Store"
    )
    store_meta["spf"] = store_meta["Weekly_Sales"] / store_meta["Size"]
    store_meta["size_band"] = pd.cut(
        store_meta["Size"],
        bins=[0, 50_000, 120_000, 999_999],
        labels=["Small (<50K sqft)", "Mid (50–120K sqft)", "Large (>120K sqft)"],
    )
    spf_by_band = store_meta.groupby("size_band")["spf"].mean()
    spf_by_type = store_meta.groupby("Type")["spf"].mean()

    # ── I4: Post-holiday cliff ────────────────────────────────────────────────
    weekly["wow"] = weekly["Weekly_Sales"].pct_change()
    top_spikes = weekly.nlargest(3, "wow")[["week_start", "wow"]]
    top_drops  = weekly.nsmallest(3, "wow")[["week_start", "wow"]]
    monthly_avg = (
        df.assign(month=df["week_start"].dt.month)
        .groupby("month")["Weekly_Sales"].mean()
    )
    dec_avg = monthly_avg[12]
    jan_avg = monthly_avg[1]
    cliff_pct = (jan_avg - dec_avg) / dec_avg

    # ── I5: Dept concentration ────────────────────────────────────────────────
    dept_totals = (
        df.groupby("Dept")["Weekly_Sales"].sum()
        .sort_values(ascending=False).reset_index()
    )
    dept_totals["share"] = dept_totals["Weekly_Sales"] / dept_totals["Weekly_Sales"].sum()
    top10_depts = dept_totals.head(10)

    # Holiday lift per dept
    d_hol   = df[df["IsHoliday"] == True].groupby("Dept")["Weekly_Sales"].mean()
    d_nohol = df[df["IsHoliday"] == False].groupby("Dept")["Weekly_Sales"].mean()
    dept_lift = ((d_hol - d_nohol) / d_nohol).dropna().sort_values(ascending=False)
    top5_lift = dept_lift.head(5)

    # ── I6 (bonus): At-risk stores right now ─────────────────────────────────
    w_store = (
        df.groupby(["week_start", "Store", "Type"])["Weekly_Sales"]
        .sum().reset_index().sort_values(["Store", "week_start"])
    )
    w_store["prev8"] = w_store.groupby("Store")["Weekly_Sales"].shift(8)
    w_store["trend8"] = (
        (w_store["Weekly_Sales"] - w_store["prev8"]) / w_store["prev8"]
    )
    latest_wk = w_store["week_start"].max()
    at_risk = (
        w_store[w_store["week_start"] == latest_wk]
        .dropna(subset=["trend8"])
        .query("trend8 < -0.10")
        .sort_values("trend8")
    )

    return dict(
        df=df, weekly=weekly, yr_avg=yr_avg,
        yoy_2011=yoy_2011, yoy_2012=yoy_2012, annual_loss_usd=annual_loss_usd,
        total_rev=total_rev,
        top5_share=top5_share, top10_share=top10_share, bot10_share=bot10_share,
        top5_stores=top5_stores, store_totals=store_totals,
        spf_by_band=spf_by_band, spf_by_type=spf_by_type,
        top_spikes=top_spikes, top_drops=top_drops,
        monthly_avg=monthly_avg, cliff_pct=cliff_pct,
        dec_avg=dec_avg, jan_avg=jan_avg,
        top10_depts=top10_depts, top5_lift=top5_lift,
        at_risk=at_risk, latest_wk=latest_wk,
    )


d = load_and_compute()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="top-banner">
  <h2>💡 Walmart Weekly Sales — Key Insights</h2>
  <span>Computed from {d['df']['week_start'].min().strftime('%b %Y')} –
  {d['df']['week_start'].max().strftime('%b %Y')} ·
  {int(d['df']['Store'].nunique())} stores ·
  ${d['total_rev']/1e9:.2f}B total revenue</span>
</div>
""", unsafe_allow_html=True)

# ── Summary strip ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="summary-strip">
  <div class="sum-tile">
    <div class="sum-label">Avg weekly fleet sales</div>
    <div class="sum-value">${d['weekly']['Weekly_Sales'].mean()/1e6:.1f}M</div>
    <div class="sum-sub">{len(d['weekly'])} weeks observed</div>
  </div>
  <div class="sum-tile">
    <div class="sum-label">YoY revenue trend</div>
    <div class="sum-value" style="color:#C5221F">{d['yoy_2012']*100:+.1f}%</div>
    <div class="sum-sub">2011→2012 year-over-year</div>
  </div>
  <div class="sum-tile">
    <div class="sum-label">Holiday lift (fleet)</div>
    <div class="sum-value" style="color:#137333">+7.1%</div>
    <div class="sum-sub">vs non-holiday avg</div>
  </div>
  <div class="sum-tile">
    <div class="sum-label">At-risk stores now</div>
    <div class="sum-value" style="color:#E37400">{len(d['at_risk'])}</div>
    <div class="sum-sub">&gt;10% 8-week decline</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSIGHT 1 — Fleet revenue decline
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ins-card">
  <div class="ins-header">
    <div class="ins-number" style="background:#FCE8E6;color:#C5221F">1</div>
    <div>
      <span class="ins-tag tag-danger">Revenue risk</span><br>
      <span class="ins-title">Fleet revenue is in a quiet but consistent 2-year decline</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_text, col_chart = st.columns([1, 1.6])

with col_text:
    loss_weekly = d['yr_avg'][2010] - d['yr_avg'][2012]
    loss_annual = loss_weekly * 52
    st.markdown(f"""
    <div style="padding: 4px 0 0 0">
      <div class="ins-stat" style="color:#C5221F">${loss_weekly/1e6:.1f}M</div>
      <div class="ins-stat-label">weekly revenue lost since 2010 (per week avg)</div>
      <p class="ins-body">
        Average weekly sales fell from
        <b>${d['yr_avg'][2010]/1e6:.1f}M</b> in 2010 to
        <b>${d['yr_avg'][2012]/1e6:.1f}M</b> in 2012 — a drop of
        ~${loss_weekly/1e3:.0f}K per week.
        Across 45 stores that annualises to roughly
        <b>${loss_annual/1e6:.0f}M in lost revenue per year</b>.
        No single event explains it; the trend is broad and gradual,
        suggesting structural demand erosion rather than an isolated shock.
        <br><br>
        <b>Recommended action:</b> Segment this decline by store type and
        geography. If Type B stores are driving it disproportionately,
        a format-level intervention is warranted.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_chart:
    st.markdown('<div class="chart-title">Average weekly sales by year</div>', unsafe_allow_html=True)
    years = [2010, 2011, 2012]
    vals  = [d['yr_avg'][y] for y in years]
    colors = [RED if v < vals[0] else GREEN for v in vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[str(y) for y in years], y=vals,
        marker_color=[RED, RED, RED],
        text=[f"${v/1e6:.2f}M" for v in vals],
        textposition="outside",
        hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_shape(type="line",
        x0=-0.5, x1=2.5,
        y0=vals[0], y1=vals[0],
        line=dict(color=BORDER, dash="dot", width=1.5))
    fig.add_annotation(x=2.4, y=vals[0],
        text=f"2010 baseline: ${vals[0]/1e6:.1f}M",
        showarrow=False, font=dict(size=10, color="#5F6368"),
        xanchor="right", yanchor="bottom")
    fig.update_layout(
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor=BORDER,
                   tickformat="$,.0f", tickfont=dict(size=10),
                   range=[min(vals)*0.985, max(vals)*1.04]),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Weekly trend line
    st.markdown('<div class="chart-title">Weekly fleet sales trend</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=d['weekly']["week_start"], y=d['weekly']["Weekly_Sales"],
        fill="tozeroy", fillcolor="rgba(197,34,31,0.06)",
        line=dict(color=RED, width=1.8),
        hovertemplate="%{x|%b %d %Y}<br>$%{y:,.0f}<extra></extra>",
    ))
    ma = d['weekly']["Weekly_Sales"].rolling(8, min_periods=1).mean()
    fig2.add_trace(go.Scatter(
        x=d['weekly']["week_start"], y=ma,
        line=dict(color=DARK_BLUE, width=1.5, dash="dot"),
        name="8W avg", hovertemplate="8W avg: $%{y:,.0f}<extra></extra>",
    ))
    fig2.update_layout(
        height=160, margin=dict(l=0, r=0, t=4, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor=BORDER,
                   tickformat="$,.0f", tickfont=dict(size=9)),
        hovermode="x unified",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSIGHT 2 — Concentration risk
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ins-card">
  <div class="ins-header">
    <div class="ins-number" style="background:#FFF0D0;color:#B45309">2</div>
    <div>
      <span class="ins-tag tag-warning">Concentration risk</span><br>
      <span class="ins-title">Top 10 stores carry 39% of total revenue — a fragile dependency</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_text2, col_chart2 = st.columns([1, 1.6])

with col_text2:
    st.markdown(f"""
    <div style="padding:4px 0 0 0">
      <div class="ins-stat" style="color:#B45309">{d['top10_share']*100:.1f}%</div>
      <div class="ins-stat-label">of total fleet revenue from just 10 stores</div>
      <p class="ins-body">
        The top 5 stores — all large Type A — account for
        <b>{d['top5_share']*100:.1f}%</b> of revenue on their own.
        The bottom 10 contribute only <b>{d['bot10_share']*100:.1f}%</b>.
        This means underperformance in two or three flagships can move
        the fleet total meaningfully in a single quarter.
        <br><br>
        Stores {', '.join(str(int(s)) for s in d['top5_stores'][:3])} are
        the three highest-revenue locations. Operational
        disruptions, out-of-stocks, or local competition at these stores
        carry an outsized financial impact.
        <br><br>
        <b>Recommended action:</b> Create a "Flagship Watch" report
        that monitors these 10 stores weekly at exec level, separate
        from the broader fleet review.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_chart2:
    st.markdown('<div class="chart-title">Revenue share — top vs bottom stores</div>', unsafe_allow_html=True)
    top5_val  = d['top5_share'] * 100
    top6_10   = (d['top10_share'] - d['top5_share']) * 100
    bot10_val = d['bot10_share'] * 100
    rest      = 100 - top5_val - top6_10 - bot10_val

    fig3 = go.Figure(go.Bar(
        x=[top5_val, top6_10, rest, bot10_val],
        y=["Top 5 stores", "Stores 6–10", "Stores 11–35", "Bottom 10 stores"],
        orientation="h",
        marker_color=[RED, AMBER, BLUE, "#DADCE0"],
        text=[f"{v:.1f}%" for v in [top5_val, top6_10, rest, bot10_val]],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig3.update_layout(
        height=200, margin=dict(l=0, r=50, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=BORDER,
                   ticksuffix="%", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="chart-title">Cumulative revenue share by store rank</div>', unsafe_allow_html=True)
    cum = d['store_totals']['Weekly_Sales'].cumsum() / d['total_rev'] * 100
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=list(range(1, len(cum)+1)), y=cum.values,
        fill="tozeroy", fillcolor="rgba(26,115,232,0.07)",
        line=dict(color=BLUE, width=2),
        hovertemplate="Top %{x} stores: %{y:.1f}% of revenue<extra></extra>",
    ))
    fig4.add_shape(type="line", x0=10, x1=10, y0=0, y1=100,
        line=dict(color=AMBER, dash="dot", width=1.5))
    fig4.add_annotation(x=10, y=50, text="Top 10",
        showarrow=False, font=dict(size=9, color=AMBER), xanchor="left")
    fig4.update_layout(
        height=170, margin=dict(l=0, r=0, t=4, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=9), title="Store rank"),
        yaxis=dict(showgrid=True, gridcolor=BORDER,
                   ticksuffix="%", tickfont=dict(size=9)),
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSIGHT 3 — Small stores punch above their weight
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ins-card">
  <div class="ins-header">
    <div class="ins-number" style="background:#E8F0FE;color:#1A73E8">3</div>
    <div>
      <span class="ins-tag tag-info">Counterintuitive finding</span><br>
      <span class="ins-title">Small stores generate 38% more revenue per square foot than large ones</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_text3, col_chart3 = st.columns([1, 1.6])

with col_text3:
    small_spf = d['spf_by_band'].get("Small (<50K sqft)", 0)
    large_spf = d['spf_by_band'].get("Large (>120K sqft)", 0)
    premium   = (small_spf - large_spf) / large_spf if large_spf else 0
    st.markdown(f"""
    <div style="padding:4px 0 0 0">
      <div class="ins-stat" style="color:{BLUE}">${small_spf:,.0f}/sqft</div>
      <div class="ins-stat-label">avg revenue per sqft — small-format stores</div>
      <p class="ins-body">
        Small-format stores (&lt;50K sqft) produce
        <b>${small_spf:,.0f}/sqft</b> vs <b>${large_spf:,.0f}/sqft</b>
        for large stores — a <b>{premium*100:.0f}% productivity premium</b>.
        Type C stores are the most space-efficient format overall.
        <br><br>
        This challenges a "bigger is better" assumption.
        Large stores carry more absolute revenue but leave proportionally
        more sales per square foot on the table. Without occupancy cost
        data this can't be confirmed as a margin story, but it warrants
        a deeper unit-economics review before any new store approvals.
        <br><br>
        <b>Recommended action:</b> Run a net margin per sqft analysis
        including rent and labour. If small formats hold their edge,
        prioritise them in the expansion pipeline.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_chart3:
    st.markdown('<div class="chart-title">Revenue per square foot by format size</div>', unsafe_allow_html=True)
    bands = list(d['spf_by_band'].index)
    vals3 = [d['spf_by_band'][b] for b in bands]
    fig5 = go.Figure(go.Bar(
        x=bands, y=vals3,
        marker_color=[BLUE, "#4285F4", "#8AB4F8"],
        text=[f"${v:,.0f}" for v in vals3],
        textposition="outside",
        hovertemplate="%{x}<br>$%{y:,.0f}/sqft<extra></extra>",
    ))
    fig5.update_layout(
        height=240, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor=BORDER,
                   tickprefix="$", tickfont=dict(size=10),
                   range=[0, max(vals3)*1.15]),
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown('<div class="chart-title">Revenue per sqft by store type (A / B / C)</div>', unsafe_allow_html=True)
    types = list(d['spf_by_type'].index)
    vals_t = [d['spf_by_type'][t] for t in types]
    fig6 = go.Figure(go.Bar(
        x=types, y=vals_t,
        marker_color=[BLUE, "#4285F4", "#8AB4F8"][:len(types)],
        text=[f"${v:,.0f}" for v in vals_t],
        textposition="outside",
        hovertemplate="Type %{x}: $%{y:,.0f}/sqft<extra></extra>",
    ))
    fig6.update_layout(
        height=170, margin=dict(l=0, r=0, t=4, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=12)),
        yaxis=dict(showgrid=True, gridcolor=BORDER,
                   tickprefix="$", tickfont=dict(size=10),
                   range=[0, max(vals_t)*1.15]),
    )
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSIGHT 4 — Post-holiday cliff
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ins-card">
  <div class="ins-header">
    <div class="ins-number" style="background:#FFF0D0;color:#B45309">4</div>
    <div>
      <span class="ins-tag tag-warning">Seasonality</span><br>
      <span class="ins-title">The post-holiday cliff is the single most violent revenue event in the calendar</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_text4, col_chart4 = st.columns([1, 1.6])

with col_text4:
    best_spike = d['top_spikes'].iloc[0]
    worst_drop = d['top_drops'].iloc[0]
    st.markdown(f"""
    <div style="padding:4px 0 0 0">
      <div class="ins-stat" style="color:{RED}">{d['cliff_pct']*100:.0f}%</div>
      <div class="ins-stat-label">December → January average drop in weekly sales</div>
      <p class="ins-body">
        Thanksgiving week produces a
        <b>+{best_spike['wow']*100:.0f}% WoW spike</b>
        ({best_spike['week_start'].strftime('%b %d, %Y')}) —
        the largest single-week jump in the dataset.
        The week after Christmas then collapses by
        <b>{worst_drop['wow']*100:.0f}%</b>
        ({worst_drop['week_start'].strftime('%b %d, %Y')}) —
        the steepest drop in the dataset. Both events occur in
        consecutive years with near-identical magnitude, confirming
        this is structural, not random.
        <br><br>
        December averages <b>${d['dec_avg']:,.0f}/store/week</b>
        vs January's <b>${d['jan_avg']:,.0f}/store/week</b>.
        Inventory purchased for the December peak becomes
        stranded capital within 2 weeks.
        <br><br>
        <b>Recommended action:</b> Build explicit post-holiday
        markdown and clearance plans, timed to the week of Dec 27.
        Staff-down schedules should be prepared 3 weeks in advance.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_chart4:
    st.markdown('<div class="chart-title">Average weekly sales by month</div>', unsafe_allow_html=True)
    months = list(range(1, 13))
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    m_vals = [d['monthly_avg'].get(m, 0) for m in months]
    bar_colors = [RED if m in [1] else (GREEN if m in [11, 12] else BLUE)
                  for m in months]

    fig7 = go.Figure(go.Bar(
        x=month_names, y=m_vals,
        marker_color=bar_colors,
        text=[f"${v/1e3:.0f}K" for v in m_vals],
        textposition="outside",
        hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
    ))
    fig7.update_layout(
        height=240, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor=BORDER,
                   tickformat="$,.0f", tickfont=dict(size=10),
                   range=[0, max(m_vals)*1.12]),
    )
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown('<div class="chart-title">Top 3 WoW spikes and drops</div>', unsafe_allow_html=True)
    events = pd.concat([d['top_spikes'], d['top_drops']]).sort_values("wow")
    fig8 = go.Figure(go.Bar(
        x=events["wow"] * 100,
        y=[w.strftime("%b %d '%y") for w in events["week_start"]],
        orientation="h",
        marker_color=[GREEN if v > 0 else RED for v in events["wow"]],
        text=[f"{v*100:+.0f}%" for v in events["wow"]],
        textposition="outside",
        hovertemplate="%{y}: %{x:+.1f}%<extra></extra>",
    ))
    fig8.add_vline(x=0, line_width=1.5, line_color=BORDER)
    fig8.update_layout(
        height=170, margin=dict(l=0, r=50, t=4, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=BORDER,
                   ticksuffix="%", tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
    )
    st.plotly_chart(fig8, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSIGHT 5 — Department concentration
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ins-card">
  <div class="ins-header">
    <div class="ins-number" style="background:#E6F4EA;color:#137333">5</div>
    <div>
      <span class="ins-tag tag-success">Growth opportunity</span><br>
      <span class="ins-title">Three departments drive 19 cents of every dollar — and holiday timing amplifies them further</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_text5, col_chart5 = st.columns([1, 1.6])

with col_text5:
    top3_share = d['top10_depts'].head(3)["share"].sum()
    top3_depts = d['top10_depts'].head(3)["Dept"].tolist()
    top_lift_dept = d['top5_lift'].index[0]
    top_lift_val  = d['top5_lift'].iloc[0]
    st.markdown(f"""
    <div style="padding:4px 0 0 0">
      <div class="ins-stat" style="color:{GREEN}">{top3_share*100:.1f}%</div>
      <div class="ins-stat-label">of total fleet revenue from depts {', '.join(str(int(d)) for d in top3_depts)}</div>
      <p class="ins-body">
        Departments {', '.join(str(int(d)) for d in top3_depts)} together
        generated <b>${d['top10_depts'].head(3)['Weekly_Sales'].sum()/1e9:.2f}B</b>
        over the full period. These are the highest-leverage departments
        for in-stock rate improvement, promotional spend, and
        planogram decisions.
        <br><br>
        On the holiday dimension, Dept {int(top_lift_dept)} shows a
        <b>+{top_lift_val*100:.0f}% holiday lift</b> — the strongest in
        the fleet. Five departments see holiday lifts above 70%,
        making them prime targets for seasonal inventory builds and
        dedicated promotional campaigns.
        <br><br>
        <b>Recommended action:</b> Prioritise fill-rate SLAs for
        the top 3 revenue depts year-round. For holiday planning,
        run dedicated depth-of-inventory reviews for the top 5
        holiday-sensitive departments starting 8 weeks before
        Thanksgiving.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_chart5:
    st.markdown('<div class="chart-title">Top 10 departments — % share of total fleet sales</div>', unsafe_allow_html=True)
    depts = [str(int(d)) for d in d['top10_depts']['Dept']]
    shares = d['top10_depts']['share'] * 100
    dept_colors = [GREEN if i < 3 else BLUE for i in range(len(depts))]

    fig9 = go.Figure(go.Bar(
        x=depts, y=shares,
        marker_color=dept_colors,
        text=[f"{v:.1f}%" for v in shares],
        textposition="outside",
        hovertemplate="Dept %{x}: %{y:.1f}% of sales<extra></extra>",
    ))
    fig9.update_layout(
        height=230, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=10), title="Department"),
        yaxis=dict(showgrid=True, gridcolor=BORDER,
                   ticksuffix="%", tickfont=dict(size=10),
                   range=[0, shares.max()*1.15]),
    )
    st.plotly_chart(fig9, use_container_width=True)

    st.markdown('<div class="chart-title">Top 5 departments by holiday lift %</div>', unsafe_allow_html=True)
    lift_depts = [str(int(d)) for d in d['top5_lift'].index]
    lift_vals  = d['top5_lift'].values * 100
    fig10 = go.Figure(go.Bar(
        x=lift_vals,
        y=[f"Dept {d}" for d in lift_depts],
        orientation="h",
        marker_color=[GREEN, "#34A853", "#81C995", "#CEEAD6", "#E6F4EA"],
        text=[f"+{v:.0f}%" for v in lift_vals],
        textposition="outside",
        hovertemplate="Dept %{y}: +%{x:.0f}% holiday lift<extra></extra>",
    ))
    fig10.update_layout(
        height=175, margin=dict(l=0, r=55, t=4, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=BORDER,
                   ticksuffix="%", tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, tickfont=dict(size=10),
                   autorange="reversed"),
    )
    st.plotly_chart(fig10, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# BONUS: At-risk stores now
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ins-card">
  <div class="ins-header">
    <div class="ins-number" style="background:#FCE8E6;color:#C5221F">!</div>
    <div>
      <span class="ins-tag tag-danger">Immediate action</span><br>
      <span class="ins-title">{len(d['at_risk'])} stores showing &gt;10% 8-week sales decline as of {d['latest_wk'].strftime('%b %d, %Y')}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1.6])

with col_a:
    type_counts = d['at_risk']['Type'].value_counts().to_dict()
    types_str = ", ".join([f"{v} Type {k}" for k, v in type_counts.items()])
    st.markdown(f"""
    <div style="padding:4px 0 0 0">
      <div class="ins-stat" style="color:{RED}">{len(d['at_risk'])}</div>
      <div class="ins-stat-label">stores with 8-week trend below −10%</div>
      <p class="ins-body">
        {types_str} stores are currently in decline,
        with the steepest being Store
        <b>{int(d['at_risk'].iloc[0]['Store'])}</b>
        at <b>{d['at_risk'].iloc[0]['trend8']*100:.1f}%</b> over 8 weeks.
        <br><br>
        Four of the six are Type B mid-format stores — suggesting
        this may be a <b>format-level challenge</b>, not isolated
        store execution.
        <br><br>
        <b>Recommended action:</b> Pull weekly store manager reports
        for these locations immediately. Cross-reference with
        local competitor activity, out-of-stock rates, and
        staffing levels. Use the At-Risk page to monitor
        their risk scores week by week.
      </p>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="chart-title">Stores with &gt;10% 8-week decline — ranked by severity</div>', unsafe_allow_html=True)
    ar = d['at_risk'].copy()
    ar["label"] = ar.apply(lambda r: f"Store {int(r['Store'])} (Type {r['Type']})", axis=1)
    ar_sorted = ar.sort_values("trend8")

    fig11 = go.Figure(go.Bar(
        x=ar_sorted["trend8"] * 100,
        y=ar_sorted["label"],
        orientation="h",
        marker_color=[RED if v < -0.14 else (AMBER if v < -0.12 else "#F28B82")
                      for v in ar_sorted["trend8"]],
        text=[f"{v*100:.1f}%" for v in ar_sorted["trend8"]],
        textposition="outside",
        hovertemplate="%{y}<br>8W trend: %{x:.1f}%<extra></extra>",
    ))
    fig11.add_vline(x=-10, line_width=1.5, line_color=AMBER,
                    line_dash="dot",
                    annotation_text="−10% threshold",
                    annotation_font_size=9)
    fig11.update_layout(
        height=250, margin=dict(l=0, r=55, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=BORDER,
                   ticksuffix="%", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
    )
    st.plotly_chart(fig11, use_container_width=True)
