import streamlit as st
import plotly.express as px

from utils import PROJECT_ID, DATASET, run_query, render_global_filters

st.title("Holiday / Seasonality")

_ = render_global_filters()

holiday_query = f"""
SELECT
  h.store_id,
  h.dept_id,
  h.avg_holdiay_sales,
  h.avg_non_holiday_sales,
  h.holiday_delta,
  h.holiday_lift_pct,
  h.total_holiday_sales,
  h.total_non_holiday_sales,
  h.holiday_weeks,
  h.non_holiday_weeks,
  s.store_type,
  s.store_size
FROM `{PROJECT_ID}.{DATASET}.vw_holiday_lift` h
LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_store` s
  ON h.store_id = s.store_id
"""

df = run_query(holiday_query)

if df.empty:
    st.warning("No holiday data available.")
    st.stop()

st.subheader("Top Holiday-Sensitive Stores")
top_stores = df.groupby(["store_id", "store_type"], as_index=False)["holiday_lift_pct"].mean()
top_stores = top_stores.sort_values("holiday_lift_pct", ascending=False).head(15)

fig = px.bar(
    top_stores,
    x="store_id",
    y="holiday_lift_pct",
    color="store_type",
    title="Top Stores by Holiday Lift",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Top Holiday-Sensitive Departments")
top_depts = df.groupby("dept_id", as_index=False)["holiday_lift_pct"].mean()
top_depts = top_depts.sort_values("holiday_lift_pct", ascending=False).head(15)

fig2 = px.bar(
    top_depts,
    x="dept_id",
    y="holiday_lift_pct",
    title="Top Departments by Holiday Lift",
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Holiday Lift Distribution")
fig3 = px.histogram(
    df,
    x="holiday_lift_pct",
    nbins=40,
    title="Distribution of Holiday Lift",
)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Detailed Holiday Lift Table")
st.dataframe(df.sort_values("holiday_lift_pct", ascending=False), use_container_width=True)