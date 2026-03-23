CREATE OR REPLACE VIEW `walmart-kpi-executive.walmart_sales_stores.vw_holiday_lift` AS 
WITH base AS (
SELECT 
  store_id,
  dept_id,
  is_holiday,
  weekly_sales
FROM `walmart-kpi-executive.walmart_sales_stores.fct_weekly_sales`
),
agg AS (
  SELECT 
    store_id, 
    dept_id,
    AVG(IF(is_holiday, weekly_sales, NULL)) AS avg_holdiay_sales,
    AVG(IF(NOT is_holiday, weekly_sales, NULL)) AS avg_non_holiday_sales,
    SUM(IF(is_holiday, weekly_sales, 0)) AS total_holiday_sales,
    SUM(IF(NOT is_holiday, weekly_sales, 0)) AS total_non_holiday_sales,
    COUNTIF(is_holiday) AS holiday_weeks,
    COUNTIF(NOT is_holiday) AS non_holiday_weeks
  FROM base
  GROUP BY 1, 2
)
SELECT 
  store_id,
  dept_id,
  avg_holdiay_sales,
  avg_non_holiday_sales,
  avg_holdiay_sales - avg_non_holiday_sales AS holiday_delta,
  SAFE_DIVIDE(avg_holdiay_sales - avg_non_holiday_sales , avg_non_holiday_sales) AS holiday_lift_pct,
  total_holiday_sales,
  total_non_holiday_sales,
  holiday_weeks,
  non_holiday_weeks
FROM agg

