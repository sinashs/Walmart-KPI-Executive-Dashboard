WITH base AS(
SELECT 
  week_start_date,
  SUM(weekly_sales) AS total_sales,
  COUNT(DISTINCT store_id) AS active_stores,
  AVG(CASE WHEN is_holiday THEN weekly_sales END) AS avg_holiday_sales,
  AVG(CASE WHEN NOT is_holiday THEN weekly_sales END) AS avg_non_holiday_sales,
FROM `{project_id}.{dataset}.vw_weekly_sales_store`
{where_clause}
GROUP BY 1
),
final AS(
  SELECT 
    week_start_date,
    total_sales,
    active_stores,
    SAFE_DIVIDE(total_sales, active_stores) AS sales_per_store,
    SAFE_DIVIDE(
      total_sales - LAG(total_sales) OVER (ORDER BY week_start_date),
      LAG(total_sales) OVER (ORDER BY week_start_date)
    ) AS wow_growth,
    SAFE_DIVIDE(
      total_sales - LAG(total_sales, 52) OVER (ORDER BY week_start_date),
      LAG(total_sales, 52) OVER (ORDER BY week_start_date) 
    ) AS yoy_growth,
    total_sales - AVG(total_sales) OVER (
      ORDER BY week_start_date
      ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS ma4_sales,
    SAFE_DIVIDE(
      STDDEV_SAMP(total_sales) OVER (
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      ),
      AVG(total_sales) OVER (
        ORDER BY week_start_date
        ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
      )
    ) AS volatility_index,
    SAFE_DIVIDE(
      avg_holiday_sales - avg_non_holiday_sales,
      avg_non_holiday_sales
    ) AS holiday_lift_pct
  FROM base
)
SELECT * 
FROM final 
ORDER BY week_start_date

