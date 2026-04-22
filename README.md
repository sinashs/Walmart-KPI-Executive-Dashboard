# 🛒 Walmart Weekly Sales Executive Dashboard

### KPI Framework + Executive Analytics | BigQuery + SQL + Streamlit + Plotly

A Business Intelligence project that transforms raw operational sales data into executive-ready insights, KPI governance, and proactive risk monitoring.

## Live Dashboard
[View the Streamlit Dashboard](https://walmart-executive-dashboard.streamlit.app/)

## Live Dashboard
🚀 <a href="https://walmart-executive-dashboard.streamlit.app/" target="_blank" rel="noopener noreferrer"><strong>Open Interactive Dashboard</strong></a>


This project demonstrates a full BI workflow:

### Data Warehouse → SQL Modeling → KPI Views → Streamlit Dashboard

I first used **Google Cloud BigQuery** to build curated views and SQL logic for business metrics, then embedded those KPI queries into a **Streamlit** application for interactive executive dashboards.

---

# 📌 Business Objective

Executives don’t need spreadsheets — they need decisions.

This dashboard helps leadership answer:

* How did we perform this week?
* What changed vs last week / last year?
* Which stores are outperforming or declining?
* Where should we intervene immediately?
* Are our KPIs trusted and clearly defined?

---

# 🧰 Tech Stack

| Tool                  | Purpose                           |
| --------------------- | --------------------------------- |
| Google Cloud BigQuery | Data warehouse + SQL metric layer |
| SQL                   | KPI logic + views + calculations  |
| Python                | Application logic                 |
| Streamlit             | Multi-page analytics app          |
| Plotly                | Interactive executive visuals     |
| Pandas                | Local data handling               |

---

# 🏗️ End-to-End Architecture

```text id="2yk3bp"
Raw Walmart Data
      ↓
BigQuery Tables
      ↓
SQL Views / KPI Logic
      ↓
Python + Streamlit App
      ↓
Executive Dashboard Pages
```

---

# 📂 Project Structure

```text id="n1es9h"
Walmart-Dashboard/
│
├── app.py
├── metric_dictionary.md
└── pages/
    ├── page1_executive_kpis.py
    ├── page2_top_movers.py
    ├── page3_at_risk.py
    └── page4_metric_dictionary.py
```

---

# 🧠 SQL / BigQuery Layer (Important)

Before building the dashboard UI, I designed the KPI logic in **BigQuery**.

That included creating reusable SQL views for:

### Executive Metrics

* Total Weekly Sales
* Active Stores
* Sales per Store
* WoW Growth %
* YoY Growth %
* Moving Average Sales

### Performance Drivers

* Top Movers
* Store Contribution
* Department Contribution
* Revenue Deltas

### Risk Modeling

* 8-week declining trends
* Revenue volatility
* Composite risk scores
* Store prioritization

### Seasonality

* Holiday lift %
* Holiday vs non-holiday performance

After validating the logic in SQL, those queries were integrated into the Streamlit app.

This mirrors real BI team workflows:
**warehouse first, dashboard second.**

---

# 🚀 Dashboard Pages

## 1️⃣ Executive KPIs

Leadership snapshot of weekly performance.

Includes:

* Total Weekly Sales
* Active Stores
* WoW Growth
* YoY Growth
* Holiday Lift
* Sales Trend
* Store Type Mix
* Volatility Index

Built in `page1_executive_kpis.py` 

---

## 2️⃣ Top Movers

Explains what drove change.

Includes:

* Store rankings
* Top gainers / decliners
* Department contribution
* Department growth shifts
* Store trends

Built in `page2_top_movers.py` 

---

## 3️⃣ At-Risk Stores

Prioritization dashboard using weighted risk logic.

Risk Formula:

```text id="9v8j5z"
50% Trend Decline
30% Volatility
20% Recent WoW Drop
```

Built in `page3_at_risk.py` 

---

## 4️⃣ Metric Dictionary

Single source of truth for definitions and formulas.

Built in `page4_metric_dictionary.py` 

---

# 📊 Key Business Insights from the Dashboard

## 📈 Holiday Weeks Create Revenue Lift

Holiday periods consistently outperform non-holiday weeks.

### Action:

Increase labor scheduling, marketing spend, and inventory before holiday weeks.

---

## 🏬 Few Stores Drive Large Revenue Share

Top stores contribute disproportionately to total revenue.

### Action:

Use high-performing stores as operating benchmarks.

---

## 📉 Volatility Predicts Future Risk

Stores with unstable revenue patterns appear more often in the At-Risk dashboard.

### Action:

Use volatility as an early warning KPI.

---

## 🔻 Short-Term + Long-Term Decline = Highest Risk

Stores down this week and down over 8 weeks rank highest in risk scores.

### Action:

Prioritize intervention on structurally weak stores.

---

## 📆 Moving Averages Reveal Real Trend

Weekly raw revenue fluctuates, but smoothed trends reveal momentum.

### Action:

Use rolling averages in executive reporting.

---

# 📌 Example Metrics

| Metric             | Definition                     |
| ------------------ | ------------------------------ |
| Total Weekly Sales | SUM(Weekly_Sales)              |
| WoW Growth         | Current Week vs Previous Week  |
| YoY Growth         | Same Week Prior Year           |
| Holiday Lift       | Holiday Avg vs Non-Holiday Avg |
| Volatility Index   | Std Dev ÷ Avg Sales            |
| Risk Score         | Weighted decline model         |

---

# 🧠 Skills Demonstrated

## Business Intelligence

Turning raw data into decisions.

## Data Warehousing

BigQuery modeling, reusable views, scalable SQL.

## Executive Storytelling

Dashboards built for leadership.

## Advanced Analytics

Risk scoring + anomaly prioritization.

## Product Thinking

Pages designed around stakeholder questions.

## Python Engineering

Reusable Streamlit architecture.

---

# ▶️ Run Locally

```bash id="6e4cl0"
pip install streamlit pandas plotly numpy google-cloud-bigquery
streamlit run app.py
```

---

# 💼 Why This Project Stands Out

Many portfolios show charts.

This project demonstrates the full BI lifecycle:

* Build warehouse logic in BigQuery
* Define metrics in SQL
* Create reusable KPI views
* Deliver dashboards in Streamlit
* Surface insights for leadership

That is real Business Intelligence.

---

# 🔮 Future Enhancements

* Live BigQuery connection
* Looker Studio production version
* Real-time ETL pipeline
* Forecasting model
* Email alerts for risk stores
* Geographic store map

---

# 👤 About Me

Business Intelligence Analyst focused on:

* KPI Systems
* Executive Dashboards
* SQL + Python Automation
* Product / Operations Analytics
* Data Storytelling

---

# 📬 Let’s Connect

Open to BI / Product Analyst / Analytics opportunities.
