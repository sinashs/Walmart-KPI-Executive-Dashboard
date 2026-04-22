WITH by_store AS(
SELECT 
  week_start_date,
  store_id,
  SUM(weekly_sales) AS total_sales
FROM `walmart-kpi-executive.walmart_sales_stores.vw_weekly_sales_store`
GROUP BY 1 , 2)

,pre_week AS(
SELECT 
  week_start_date,
  store_id,
  total_sales,
  total_sales - LAG(total_sales) OVER (PARTITION BY store_id ORDER BY week_start_date) AS delta_sales
FROM by_store
)
SELECT 
  week_start_date,
  store_id,
  total_sales,
  delta_sales
FROM pre_week