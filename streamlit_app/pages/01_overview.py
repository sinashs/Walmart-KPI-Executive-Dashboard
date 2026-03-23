import streamlit as st
import plotly.express as px

from utils import (
    PROJECT_ID,
    DATASET,
    run_query,
    render_global_filters,
    build_where_clause,
    format_currency,
    format_pct,
)

st.title("Executive Overview")

filters = render_global_filters()

where_clause = build_where_clause(
    start_date=filters["start_date"],
    end_date=filters["end_date"],
    store_type=filters["store_type"],
    store_ids=filters["store_ids"],
    dept_ids=filters["dept_ids"],
)

kpi_query = f"""
WITH base AS (
  SELECT
    week_start_date,
    SUM(weekly_sales) AS total_sales,
    COUNT(DISTINCT store_id) AS active_stores,
    AVG(CASE WHEN is_holiday THEN weekly_sales END) AS avg_holiday_sales,
    AVG(CASE WHEN NOT is_holiday THEN weekly_sales END) AS avg_non_holiday_sales
  FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
  {where_clause}
  GROUP BY 1
),
final AS (
  SELECT
    week_start_date,
    total_sales,
    active_stores,
    SAFE_DIVIDE(total_sales, active_stores) AS sales_per_store,
    SAFE_DIVIDE(
      total_sales - LAG(total_sales) OVER (ORDER BY week_start_date),
      LAG(total_sales) OVER (ORDER BY week_start_date)
    ) AS wow_growth,
    SAFE_DIVIDE(
      total_sales - LAG(total_sales, 52) OVER (ORDER BY week_start_date),
      LAG(total_sales, 52) OVER (ORDER BY week_start_date)
    ) AS yoy_growth,
    AVG(total_sales) OVER (
      ORDER BY week_start_date
      ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS ma4_sales,
    SAFE_DIVIDE(
      STDDEV_SAMP(total_sales) OVER (
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      ),
      AVG(total_sales) OVER (
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      )
    ) AS volatility_index,
    SAFE_DIVIDE(avg_holiday_sales - avg_non_holiday_sales, avg_non_holiday_sales) AS holiday_lift_pct
  FROM base
)
SELECT *
FROM final
ORDER BY week_start_date
"""

df = run_query(kpi_query)

if df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

latest = df.iloc[-1]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Weekly Sales", format_currency(latest["total_sales"]))
col2.metric("WoW Growth", format_pct(latest["wow_growth"]))
col3.metric("YoY Growth", format_pct(latest["yoy_growth"]))
col4.metric("Holiday Lift", format_pct(latest["holiday_lift_pct"]))
col5.metric("Volatility Index", f"{latest['volatility_index']:.2f}" if latest["volatility_index"] is not None else "—")

st.subheader("Weekly Sales Trend")
fig = px.line(
    df,
    x="week_start_date",
    y=["total_sales", "ma4_sales"],
    labels={"value": "Sales", "week_start_date": "Week"},
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Top Movers by Store")
store_movers_query = f"""
WITH by_store AS (
  SELECT
    week_start_date,
    store_id,
    SUM(weekly_sales) AS sales
  FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
  {where_clause}
  GROUP BY 1, 2
),
ranked AS (
  SELECT
    *,
    sales - LAG(sales) OVER (PARTITION BY store_id ORDER BY week_start_date) AS delta_sales
  FROM by_store
)
SELECT
  week_start_date,
  store_id,
  sales,
  delta_sales
FROM ranked
WHERE delta_sales IS NOT NULL
ORDER BY ABS(delta_sales) DESC
LIMIT 15
"""
movers_df = run_query(store_movers_query)
st.dataframe(movers_df, use_container_width=True)

st.subheader("At-Risk Stores")
risk_query = f"""
WITH by_store_week AS (
  SELECT
    week_start_date,
    store_id,
    SUM(weekly_sales) AS sales
  FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
  {where_clause}
  GROUP BY 1, 2
),
features AS (
  SELECT
    week_start_date,
    store_id,
    sales,
    SAFE_DIVIDE(
      sales - LAG(sales, 8) OVER (PARTITION BY store_id ORDER BY week_start_date),
      LAG(sales, 8) OVER (PARTITION BY store_id ORDER BY week_start_date)
    ) AS trend_8wk,
    SAFE_DIVIDE(
      STDDEV_SAMP(sales) OVER (
        PARTITION BY store_id
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      ),
      AVG(sales) OVER (
        PARTITION BY store_id
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      )
    ) AS volatility,
    SAFE_DIVIDE(
      sales - LAG(sales) OVER (PARTITION BY store_id ORDER BY week_start_date),
      LAG(sales) OVER (PARTITION BY store_id ORDER BY week_start_date)
    ) AS wow_growth
  FROM by_store_week
),
latest_week AS (
  SELECT MAX(week_start_date) AS max_week
  FROM by_store_week
)
SELECT
  f.week_start_date,
  f.store_id,
  f.sales,
  f.trend_8wk,
  f.volatility,
  f.wow_growth,
  (
    50 * COALESCE(ABS(LEAST(f.trend_8wk, 0)), 0) +
    30 * COALESCE(f.volatility, 0) +
    20 * COALESCE(ABS(LEAST(f.wow_growth, 0)), 0)
  ) AS at_risk_score
FROM features f
CROSS JOIN latest_week lw
WHERE f.week_start_date = lw.max_week
ORDER BY at_risk_score DESC
LIMIT 15
"""
risk_df = run_query(risk_query)
st.dataframe(risk_df, use_container_width=True)