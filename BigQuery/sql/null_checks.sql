SELECT 
  COUNTIF(store_id IS NULL) AS null_store,
  COUNTIF(dept_id IS NULL) AS null_dept,
  COUNTIF(week_start_date IS NULL) AS null_week,
  COUNTIF(weekly_sales IS NULL ) AS null_sales
FROM `walmart-kpi-executive.walmart_sales_stores.fct_weekly_sales`