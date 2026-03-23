import streamlit as st
import plotly.express as px

from utils import (
    PROJECT_ID,
    DATASET,
    run_query,
    render_global_filters,
    build_where_clause,
)

st.title("Store Performance")

filters = render_global_filters()

where_clause = build_where_clause(
    start_date=filters["start_date"],
    end_date=filters["end_date"],
    store_type=filters["store_type"],
    store_ids=filters["store_ids"],
    dept_ids=filters["dept_ids"],
)

query = f"""
WITH by_store_week AS (
  SELECT
    week_start_date,
    store_id,
    store_type,
    store_size,
    SUM(weekly_sales) AS total_sales
  FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
  {where_clause}
  GROUP BY 1, 2, 3, 4
),
features AS (
  SELECT
    week_start_date,
    store_id,
    store_type,
    store_size,
    total_sales,
    SAFE_DIVIDE(total_sales, store_size) AS sales_per_sqft,
    SAFE_DIVIDE(
      total_sales - LAG(total_sales) OVER (PARTITION BY store_id ORDER BY week_start_date),
      LAG(total_sales) OVER (PARTITION BY store_id ORDER BY week_start_date)
    ) AS wow_growth,
    SAFE_DIVIDE(
      STDDEV_SAMP(total_sales) OVER (
        PARTITION BY store_id
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      ),
      AVG(total_sales) OVER (
        PARTITION BY store_id
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      )
    ) AS volatility
  FROM by_store_week
)
SELECT *
FROM features
ORDER BY week_start_date, total_sales DESC
"""

df = run_query(query)

if df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

latest_week = df["week_start_date"].max()
latest_df = df[df["week_start_date"] == latest_week].copy()

st.subheader(f"Store Leaderboard — {latest_week}")
st.dataframe(
    latest_df.sort_values("total_sales", ascending=False),
    use_container_width=True
)

st.subheader("Sales vs Size")
fig = px.scatter(
    latest_df,
    x="store_size",
    y="total_sales",
    color="store_type",
    hover_data=["store_id", "sales_per_sqft", "wow_growth", "volatility"],
    title="Store Sales vs Store Size",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Top Stores by Sales per Sqft")
top_efficiency = latest_df.sort_values("sales_per_sqft", ascending=False).head(15)
fig2 = px.bar(
    top_efficiency,
    x="store_id",
    y="sales_per_sqft",
    color="store_type",
    title="Top 15 Stores by Sales per Sqft",
)
st.plotly_chart(fig2, use_container_width=True)