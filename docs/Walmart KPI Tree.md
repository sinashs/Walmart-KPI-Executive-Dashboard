Walmart KPI Tree (Weekly Sales)
# North Star
## Total Weekly Sales ($)
(aggregate of Weekly_Sales across all stores and departments)

## Level 1 Drivers (the big levers)
1) **Sales Volume** (Store/Dept Coverage)
   - How much each store and department contributes to total sales.
2) **Growth**
   - How sales are changing over time.
3) **Seasonality & Holiday Impact**
   - How holidays shift baseline sales.
4) **Stability / Volatility (Risk)**
   - How predictable sales are (important for operations and planning).
## Level 2 KPIs (what you measure under each driver)
1) **Sales Volume**
   + Sales by Store
   + Sales by Department
   + Sales by Store Type (A/B/C from stores.csv)
   + Sales per Store (productivity proxy)
   + Sales per Square Foot (if you use store Size)

2) **Growth**
    - WoW % Change (Week-over-week)
    - YoY % Change (Year-over-year, same week number)
    - Rolling 4-week / 8-week trend
    - Top Movers (stores/depts with biggest sales increases/decreases)

3) **Seasonality & Holiday Impact**
    + Holiday Lift %
       + (Avg sales on holiday weeks – Avg non-holiday weeks) / Avg non-holiday
     + Holiday Contribution
       - % of total sales occurring during holiday weeks
     + Holiday Sensitivity by Store/Dept
         - who benefits most/least from holiday weeks

4) **Stability / Volatility (Risk)**
   + **Volatility Index**
     + std dev of sales / mean sales (per store/dept over rolling N weeks)
   + **Forecast Error proxy (optional if you build a simple forecast)**
   + **At-Risk Store/Dept Score (your “senior BI” metric)**
     + combination of declining trend + high volatility + recent negative WoW/YoY
  
## Level 3 “Action” Outputs (what leaders do with it)
   + At-risk stores/departments list (needs attention)
   + High-opportunity stores/departments list (growth or holiday lift potential)
   + Operational planning inputs
     + staffing/inventory signals based on volatility + holiday sensitivity