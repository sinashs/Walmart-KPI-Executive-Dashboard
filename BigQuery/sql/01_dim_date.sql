CREATE OR REPLACE TABLE walmart_sales_stores.dim_date AS
WITH dates AS ( 
    SELECT d AS date
    FROM UNNEST(GENERATE_DATE_ARRAY('2010-01-01', '2013-12-31', INTERVAL 1 DAY)) AS d
)
SELECT 
  Date,
  EXTRACT(YEAR FROM Date) AS year,
  EXTRACT(Quarter From Date) AS quarter,
  EXTRACT(Month FROM Date) AS month,
  FORMAT_DATE("%B", Date) AS month_name,
  EXTRACT(ISOWEEK FROM Date) AS iso_week,
  FORMAT_DATE("%Y-%m", Date) AS year_month,
  DATE_TRUNC(Date, WEEK(Monday)) AS week_start_date,

FROM `walmart-kpi-executive.walmart_sales_stores.raw_sales_50K`;