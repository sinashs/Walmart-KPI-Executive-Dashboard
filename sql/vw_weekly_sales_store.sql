CREATE OR REPLACE VIEW walmart-kpi-executive.walmart_sales_stores.vw_weekly_sales_store AS
SELECT 
  f.week_start_date,
  f.store_id,
  ds.store_type,
  ds.store_size,
  f.dept_id,
  f.weekly_sales,
  f.is_holiday
FROM `walmart_sales_stores.fct_weekly_sales` f 
LEFT JOIN `walmart_sales_stores.dim_store` ds 
ON ds.store_id = f.store_id

