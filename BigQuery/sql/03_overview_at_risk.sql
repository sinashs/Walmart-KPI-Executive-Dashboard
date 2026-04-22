CREATE OR REPLACE VIEW `walmart_sales_stores.vw_o3_overview_at_risk` AS
SELECT 
  week_start_date,
  store_id,
  store_type,
  dept_id,
  weekly_sales,
  wow_sales_change_pct,
  trend_8w_change_pct,
  volatility_cv,
  risk_score,
  risk_rank
FROM `walmart_sales_stores.vw_at_risk_rankings`
QUALIFY ROW_NUMBER() OVER(
  PARTITION BY  store_id
  ORDER BY risk_score DESC
  ) = 1
ORDER BY risk_score DESC
