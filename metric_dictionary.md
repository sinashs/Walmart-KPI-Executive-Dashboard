# Metric Dictionary — Walmart Weekly Sales (BigQuery + Streamlit)

## Data grain and core tables

**Primary fact grain:** `store_id + dept_id + week_start_date`

**Core fields:** `Weekly_Sales`, `IsHoliday`, `Store`, `Dept`, `Date`

**Store attributes:** `Type`, `Size` (from `raw_stores.csv`)

**Optional features:** `Temperature`, `Fuel_Price`, `CPI`, `Unemployment`, `MarkDown1-5` (from `raw_features.csv`)

### Key assumptions (important)

* “Week” is defined by the dataset’s `Date` (weekly observation).
* “Holiday week” is `IsHoliday = TRUE` (may not cover all holiday effects).
* Dataset contains **sales**, not profit/margin; we use sales-based proxies for performance.
---
## North Star
### 1) Total Weekly Sales ($)

* **Definition:** Total sales in a given week across all stores and departments.
* **Formula (SQL):** `SUM(Weekly_Sales)`
* **Default filters:** none
* **Grain:** week_start_date
* **Notes:** Use as the top KPI tile; always show trend.
---
## Sales volume and mix
### 2) Sales by Store ($)
* **Definition:** Total weekly sales per store.
* **Formula:** `SUM(Weekly_Sales)` grouped by `Store`
* **Grain:** store_id + week_start_date
* **Notes:** Use for leaderboards and “top movers.”
### 3) Sales by Department ($)
* **Definition:** Total weekly sales per department.
* **Formula:** `SUM(Weekly_Sales)` grouped by `Dept`
* **Grain:** dept_id + week_start_date
### 4) Sales by Store Type ($)
* **Definition:** Total weekly sales by store type (A/B/C).
* **Formula:** `SUM(Weekly_Sales)` grouped by `Type`
* **Grain:** store_type + week_start_date
* **Dependencies:** join to stores table on `Store`
### 5) Sales per Store ($/store)
* **Definition:** Average weekly sales per active store.
* **Formula:** `SUM(Weekly_Sales) / COUNT(DISTINCT Store)`
* **Grain:** week_start_date (or segment + week)
* **Notes:** Use to compare productivity over time independent of store count.
### 6) Sales per Square Foot ($/sqft)
* **Definition:** Sales normalized by store size.
* **Formula:** `SUM(Weekly_Sales) / SUM(Size)` (within chosen group)
* **Grain:** week_start_date (or store_type + week)
* **Dependencies:** stores table has `Size`
* **Notes:** Works best by store type or region-like groupings; avoid dividing per dept-store rows unless carefully aggregated.
### 7) Department Contribution (% of Sales)
* **Definition:** Share of total sales attributable to each department within a period.
* **Formula:**
  * `dept_sales = SUM(Weekly_Sales)` by Dept
  * `total_sales = SUM(Weekly_Sales)` (same filters)
  * `dept_contribution = dept_sales / total_sales`
* **Grain:** dept_id + period
* **Notes:** Use in Driver page to show which depts drive overall results.
---
## Growth
### 8) WoW Sales Growth (%)
* **Definition:** Week-over-week percent change in total sales.
* **Formula:** `(sales_this_week - sales_last_week) / sales_last_week`
* **Grain:** week_start_date
* **Implementation note:** Use `LAG(total_sales) OVER (ORDER BY week_start_date)`
* **Edge cases:** If last week sales = 0, return NULL.
### 9) YoY Sales Growth (%)
* **Definition:** Year-over-year percent change vs the same week number in prior year.
* **Formula:** `(sales_this_week - sales_same_week_last_year) / sales_same_week_last_year`
* **Grain:** week_start_date
* **Implementation note:** Use `EXTRACT(ISOWEEK FROM date)` + `EXTRACT(YEAR FROM date)` matching, or a 52-week lag approach.
* **Edge cases:** Missing prior-year week → NULL.
### 10) Rolling 4-Week Sales (MA4)
* **Definition:** 4-week moving average of total sales.
* **Formula:** `AVG(total_sales) OVER (ORDER BY week ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)`
* **Grain:** week_start_date
* **Notes:** Smooths noise; great for exec view.
### 11) Rolling 8-Week Trend Slope
* **Definition:** Simple trend indicator using last 8 weeks; can be slope or % change.
* **Option A (simple):** `(sales_current - sales_8_weeks_ago) / sales_8_weeks_ago`
* **Option B (slope):** linear regression slope in Python (more advanced).
* **Grain:** week_start_date
* **Notes:** Use for “at-risk” scoring.
### 12) Top Movers (Contribution to Change)
* **Definition:** Which stores/depts contributed most to ΔSales between two periods.
* **Formula:**
  * `delta = sales_period2 - sales_period1` by store/dept
  * sort by `ABS(delta)` or `delta`
* **Grain:** store_id or dept_id (for a chosen comparison window)
* **Notes:** This is your “why behind the numbers.”
---
## Holiday and seasonality
### 13) Holiday Sales ($)
* **Definition:** Total sales during holiday weeks.
* **Formula:** `SUM(Weekly_Sales) WHERE IsHoliday = TRUE`
* **Grain:** week_start_date (or period)
### 14) Non-Holiday Sales ($)
* **Definition:** Total sales during non-holiday weeks.
* **Formula:** `SUM(Weekly_Sales) WHERE IsHoliday = FALSE`
### 15) Holiday Lift (%)
* **Definition:** Percent lift of holiday-week sales compared to non-holiday baseline.
* **Formula:** `(avg_holiday_sales - avg_nonholiday_sales) / avg_nonholiday_sales`
* **Grain:** segment (store, dept, type) + period
* **Edge cases:** baseline = 0 → NULL
* **Notes:** Also compute by store type and dept for “sensitivity.”
### 16) Holiday Contribution (% of Total)
* **Definition:** Fraction of sales that occurs during holiday weeks.
* **Formula:** `holiday_sales / total_sales`
* **Grain:** period
### 17) Holiday Sensitivity Ranking
* **Definition:** Rank stores/depts by Holiday Lift.
* **Formula:** `RANK() OVER (ORDER BY holiday_lift DESC)` within segment.
* **Notes:** Shows where holidays matter most.
---
## Stability / volatility / risk
### 18) Volatility Index (CV)
* **Definition:** Coefficient of Variation over a rolling window (e.g., 8 weeks).
* **Formula:** `STDDEV(total_sales) / AVG(total_sales)` over rolling N weeks
* **Grain:** week_start_date (or store/dept + week)
* **Notes:** Higher = less predictable; a risk signal.
### 19) Sales Anomaly Flag
* **Definition:** Flags weeks where sales deviates strongly from recent history.
* **Formula (simple):**
  * compute rolling mean & stddev over N weeks
  * flag if `ABS(sales - mean) > 2 * stddev`
* **Grain:** week_start_date (or store/dept + week)
* **Notes:** Great for DataOps-like monitoring.
### 20) At-Risk Score (Store/Dept)
* **Definition:** Composite score to prioritize where attention is needed.
* **Suggested components (0–100 scaled):**
  * Trend decline (rolling 8-week % change)
  * High volatility (CV)
  * Recent negative WoW
  * Optional: holiday sensitivity mismatch (if holiday periods)
* **Example formula (conceptual):**
  `risk = 0.5*trend_decline_score + 0.3*volatility_score + 0.2*recent_drop_score`
* **Grain:** store_id or dept_id + current period
* **Notes:** Keep weights documented. This is your “senior signature.”
---
## Data quality / governance checks (DataOps lite)
### 21) Freshness Check
* **Definition:** Confirms latest week exists and data is up-to-date.
* **Check:** `MAX(Date)` is within expected range (for static dataset, simulate).
* **Notes:** In real pipelines, this is critical.
### 22) Uniqueness Check (Primary Key)
* **Definition:** Ensure each store+dept+week has at most one row.
* **Check:** count duplicates of `(Store, Dept, Date)` should be 0.
### 23) Completeness Check (Critical fields)
* **Definition:** No nulls in `Store, Dept, Date, Weekly_Sales`.
* **Check:** null counts = 0 (or within acceptable threshold)
---
## Naming conventions (recommended)
* Facts: `fct_...` (e.g., `fct_weekly_sales`)
* Dimensions: `dim_...` (e.g., `dim_store`)
* Curated views: `vw_...` (e.g., `vw_sales_kpis_weekly`)
* Metrics in BI: `metric_total_weekly_sales`, `metric_wow_growth`, etc.
