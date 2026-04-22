WITH weekly AS (
  SELECT 
    week_start_date,
    store_id,
    dept_id,
    SUM(weekly_sales) AS total_sales
    FROM `walmart-kpi-executive.walmart_sales_stores.fct_weekly_sales` 
  GROUP BY 1,2,3
),
pre_weekly AS(
  SELECT
  week_start_date,
  store_id,
  dept_id,
  total_sales,
  LAG(total_sales) OVER(PARTITION BY store_id, dept_id ORDER BY week_start_date) AS prev_week_sales,
  --8week trend(compare to 8 weeks ago)
  LAG(total_sales, 8) OVER(PARTITION BY store_id, dept_id ORDER BY week_start_date) AS prev_8week_sales
  FROM weekly)
  --wow sales change pct
,change_pct AS(
  SELECT 
  week_start_date,
  store_id,
  dept_id,
  total_sales,
  prev_week_sales,
  SAFE_DIVIDE(total_sales, prev_week_sales) AS wow_sales_change_pct,
  prev_8week_sales,
  SAFE_DIVIDE(total_sales, prev_8week_sales) AS trend_8w_change_pct,
  FROM pre_weekly
)

,features AS (
  SELECT 
  week_start_date,
  store_id,
  dept_id,
  --rolling 8-week volatility (CV = std/avg)
  AVG(total_sales) OVER(PARTITION BY store_id, dept_id ORDER BY week_start_date ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) AS moving_avg_8week_sales,
  STDDEV(total_sales) OVER(PARTITION BY store_id, dept_id ORDER BY week_start_date ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) AS moving_std_8week_sales
  FROM weekly
)

, scored AS (
SELECT 
  c.week_start_date,
  c.store_id,
  c.dept_id,
  SAFE_DIVIDE(f.moving_std_8week_sales, f.moving_avg_8week_sales) AS volatility_cv,
  --Simple risk scoring(0-100 ish)
  -- Trend decline: penalize nagative trend(down = higher risk)
  GREATEST(0, -c.trend_8w_change_pct) AS trend_decline_risk,
  LEAST(1, IFNULL(SAFE_DIVIDE(f.moving_std_8week_sales, f.moving_avg_8week_sales), 0)) AS volatility_risk,
  GREATEST(0, -c.wow_sales_change_pct) AS wow_sales_decline_risk,
  50 * GREATEST(0, -c.trend_8w_change_pct) +
  30 * LEAST(1, IFNULL(SAFE_DIVIDE(f.moving_std_8week_sales, f.moving_avg_8week_sales), 0)) +
  20 * GREATEST(0, -c.wow_sales_change_pct) AS risk_score, 
FROM features f
INNER JOIN change_pct c
USING(week_start_date, store_id, dept_id)
)
SELECT 
  s.week_start_date,
  s.store_id,
  d.store_type,
  s.dept_id,
  c.total_sales,
  c.wow_sales_change_pct,
  c.trend_8w_change_pct,
  s.volatility_cv,
  s.risk_score,
  --rank by risk score
  RANK() OVER(PARTITION BY s.week_start_date ORDER BY s.risk_score DESC) AS risk_rank
FROM scored s
INNER JOIN features f USING(week_start_date, store_id, dept_id)
INNER JOIN change_pct c USING(week_start_date, store_id, dept_id)
LEFT JOIN `walmart-kpi-executive.walmart_sales_stores.dim_store` d USING(store_id)
WHERE d.store_type IS NOT NULL


