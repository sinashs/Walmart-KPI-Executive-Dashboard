CREATE OR REPLACE TABLE walmart_sales_stores.dim_department AS 
SELECT DISTINCT 
  CAST(Dept AS INT64) AS dept_id
FROM `walmart-kpi-executive.walmart_sales_stores.raw_sales_50K` 
;