SELECT
  store_id, dept_id, week_start_date,
  COUNT(*) AS cnt
FROM `walmart-kpi-executive.walmart_sales_stores.fct_weekly_sales`
GROUP BY 1, 2, 3
HAVING cnt > 1