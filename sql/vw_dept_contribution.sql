CREATE OR REPLACE VIEW `walmart-kpi-executive.walmart_sales_stores.vw_dept_contribution` AS 
WITH dept_week AS(
  SELECT
    week_start_date,
    dept_id,
    SUM(weekly_sales) AS dept_sales
  FROM `walmart-kpi-executive.walmart_sales_stores.fct_weekly_sales` 
  GROUP BY 1 , 2 
),
total_week AS (
  SELECT 
    week_start_date,
    SUM(weekly_sales) AS total_sales
FROM `walmart-kpi-executive.walmart_sales_stores.fct_weekly_sales` 
  GROUP BY 1
),
joined AS (
  SELECT 
  d.week_start_date,
  d.dept_id,
  d.dept_sales,
  t.total_sales,
  SAFE_DIVIDE(d.dept_sales , t.total_sales) AS dept_share
  FROM dept_week d
  INNER JOIN total_week t USING(week_start_date) 
),
prev_week AS(
SELECT 
  week_start_date,
  dept_id,
  dept_sales,
  total_sales,
  dept_share,
  LAG(dept_sales) OVER(PARTITION BY dept_id ORDER BY week_start_date) AS prev_week_sales,
  LAG(dept_share) OVER(PARTITION BY dept_id ORDER BY week_start_date) AS prev_week_share
FROM joined j)
SELECT 
  week_start_date,
  dept_id, 
  dept_sales,
  total_sales,
  dept_share,
  prev_week_sales,
  prev_week_share,
  dept_sales - prev_week_sales AS wow_sales_change,
  SAFE_DIVIDE(dept_sales - prev_week_sales , prev_week_sales) AS wow_sales_change_pct,
  dept_share - prev_week_share AS wow_share_change
FROM prev_week

