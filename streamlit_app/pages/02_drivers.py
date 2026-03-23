import streamlit as st
import plotly.express as px
import pandas as pd

from utils import (
    PROJECT_ID,
    DATASET,
    run_query,
    render_global_filters,
    build_where_clause,
)

st.title("Drivers")

filters = render_global_filters()

where_clause = build_where_clause(
    start_date=filters["start_date"],
    end_date=filters["end_date"],
    store_type=filters["store_type"],
    store_ids=filters["store_ids"],
    dept_ids=filters["dept_ids"],
)

st.subheader("Department Contribution")
dept_query = f"""
SELECT
  week_start_date,
  dept_id,
  dept_sales,
  total_sales,
  dept_share,
  wow_sales_change,
  wow_sales_change_pct,
  wow_share_change
FROM `{PROJECT_ID}.{DATASET}.vw_dept_contribution`
"""

dept_df = run_query(dept_query)

if filters["start_date"]:
    dept_df = dept_df[dept_df["week_start_date"] >= filters["start_date"]]
if filters["end_date"]:
    dept_df = dept_df[dept_df["week_start_date"] <= filters["end_date"]]
if filters["dept_ids"]:
    dept_df = dept_df[dept_df["dept_id"].isin(filters["dept_ids"])]

top_n = st.slider("Top departments to display", min_value=5, max_value=30, value=10)

# convert numeric columns
numeric_cols = [
    "dept_sales",
    "total_sales",
    "dept_share",
    "wow_sales_change",
    "wow_sales_change_pct",
    "wow_share_change",
]

for col in numeric_cols:
    if col in dept_df.columns:
        dept_df[col] = pd.to_numeric(dept_df[col], errors="coerce")

latest_week = dept_df["week_start_date"].max()
latest_df = (
    dept_df[dept_df["week_start_date"] == latest_week]
    .sort_values("dept_sales", ascending=False)
    .head(top_n)
)

fig = px.bar(
    latest_df,
    x="dept_id",
    y="dept_share",
    title=f"Top {top_n} Department Contribution - {latest_week}",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Departments Driving Change")
change_df = latest_df.sort_values("wow_sales_change", ascending=False)
fig2 = px.bar(
    change_df,
    x="dept_id",
    y="wow_sales_change",
    title="Week-over-Week Change by Department",
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Store Type Contribution")
store_type_query = f"""
SELECT
  week_start_date,
  store_type,
  SUM(weekly_sales) AS total_sales
FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
{where_clause}
GROUP BY 1, 2
ORDER BY 1, 2
"""
store_type_df = run_query(store_type_query)

fig3 = px.area(
    store_type_df,
    x="week_start_date",
    y="total_sales",
    color="store_type",
    title="Sales Contribution by Store Type",
)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Detailed Table")
st.dataframe(latest_df, use_container_width=True)