CREATE OR REPLACE TABLE walmart_sales_stores.dim_store AS
SELECT  
  CAST(Store AS INT64) AS store_id,
  Type AS store_type,
  CAST(Size AS INT64) AS store_size
  FROM `walmart-kpi-executive.walmart_sales_stores.raw_stores`;
