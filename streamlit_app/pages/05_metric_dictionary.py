import streamlit as st

st.title("Metric Dictionary")

st.markdown(
    """
## Data Grain
- Primary fact grain: `store_id + dept_id + week_start_date`

## Core KPIs
### Total Weekly Sales
- Definition: Total sales in a given week across all stores and departments
- Formula: `SUM(Weekly_Sales)`

### WoW Sales Growth
- Formula: `(sales_this_week - sales_last_week) / sales_last_week`

### YoY Sales Growth
- Formula: `(sales_this_week - sales_same_week_last_year) / sales_same_week_last_year`

### Sales per Store
- Formula: `SUM(Weekly_Sales) / COUNT(DISTINCT Store)`

### Sales per Square Foot
- Formula: `SUM(Weekly_Sales) / SUM(Size)`

### Department Contribution
- Formula:
  - `dept_sales = SUM(Weekly_Sales)`
  - `dept_contribution = dept_sales / total_sales`

### Holiday Lift
- Formula: `(avg_holiday_sales - avg_nonholiday_sales) / avg_nonholiday_sales`

### Volatility Index
- Formula: `STDDEV(total_sales) / AVG(total_sales)`

### At-Risk Score
- Suggested logic:
  - Trend decline
  - High volatility
  - Recent negative WoW
- Example:
  - `risk = 0.5*trend_decline_score + 0.3*volatility_score + 0.2*recent_drop_score`

## Assumptions
- Week is defined by the dataset's `Date`
- Holiday week is `IsHoliday = TRUE`
- Dataset contains sales, not profit
"""
)