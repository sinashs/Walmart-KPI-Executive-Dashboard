CREATE OR REPLACE TABLE walmart_sales_stores.fct_weekly_sales 
PARTITION BY week_start_date
CLUSTER BY store_id, dept_id
AS
SELECT 
  CAST(store AS INT64) AS store_id,
  CAST(Dept AS INT64) AS dept_id,
  Date As date,
  DATE_TRUNC(Date , WEEK(MONDAY)) AS week_start_date,
  CAST(Weekly_sales AS NUMERIC) AS weekly_sales,
  CAST(IsHoliday AS BOOL) AS is_holiday
FROM `walmart-kpi-executive.walmart_sales_stores.raw_sales_50K` 
