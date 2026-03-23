from __future__ import annotations

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account


PROJECT_ID = "walmart-kpi-executive"
DATASET = "walmart_sales_stores"


@st.cache_resource
def get_bq_client():
    credentials = service_account.Credentials.from_service_account_file(
        "service-account.json"
    )
    return bigquery.Client(
        credentials=credentials,
        project=credentials.project_id
    )


@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    client = get_bq_client()
    return client.query(query).to_dataframe()


def format_currency(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"${value:,.0f}"


def format_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.2%}"


def get_min_max_dates() -> tuple[str, str]:
    query = f"""
    SELECT
      CAST(MIN(week_start_date) AS STRING) AS min_date,
      CAST(MAX(week_start_date) AS STRING) AS max_date
    FROM `{PROJECT_ID}.{DATASET}.fct_weekly_sales`
    """
    df = run_query(query)
    return df.loc[0, "min_date"], df.loc[0, "max_date"]


def build_where_clause(
    start_date: str | None = None,
    end_date: str | None = None,
    store_type: list[str] | None = None,
    store_ids: list[int] | None = None,
    dept_ids: list[int] | None = None,
) -> str:
    conditions = []

    if start_date:
        conditions.append(f"week_start_date >= DATE('{start_date}')")
    if end_date:
        conditions.append(f"week_start_date <= DATE('{end_date}')")

    if store_type:
        store_type_list = ", ".join([f"'{x}'" for x in store_type])
        conditions.append(f"store_type IN ({store_type_list})")

    if store_ids:
        store_id_list = ", ".join([str(x) for x in store_ids])
        conditions.append(f"store_id IN ({store_id_list})")

    if dept_ids:
        dept_id_list = ", ".join([str(x) for x in dept_ids])
        conditions.append(f"dept_id IN ({dept_id_list})")

    if not conditions:
        return ""

    return "WHERE " + " AND ".join(conditions)


@st.cache_data(ttl=600)
def get_filter_options():
    query = f"""
    SELECT DISTINCT store_type
    FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
    ORDER BY store_type
    """
    store_types = run_query(query)["store_type"].dropna().tolist()

    stores_query = f"""
    SELECT DISTINCT store_id
    FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
    ORDER BY store_id
    """
    store_ids = run_query(stores_query)["store_id"].dropna().tolist()

    depts_query = f"""
    SELECT DISTINCT dept_id
    FROM `{PROJECT_ID}.{DATASET}.vw_weekly_sales_store`
    ORDER BY dept_id
    """
    dept_ids = run_query(depts_query)["dept_id"].dropna().tolist()

    return store_types, store_ids, dept_ids


def render_global_filters():
    min_date, max_date = get_min_max_dates()
    store_types, store_ids, dept_ids = get_filter_options()

    st.sidebar.header("Filters")

    date_range = st.sidebar.date_input(
        "Date range",
        value=[],
        min_value=pd.to_datetime(min_date),
        max_value=pd.to_datetime(max_date),
    )

    selected_store_types = st.sidebar.multiselect("Store Type", options=store_types)
    selected_store_ids = st.sidebar.multiselect("Store ID", options=store_ids)
    selected_dept_ids = st.sidebar.multiselect("Department ID", options=dept_ids)

    start_date = None
    end_date = None

    if len(date_range) == 2:
        start_date = str(date_range[0])
        end_date = str(date_range[1])

    return {
        "start_date": start_date,
        "end_date": end_date,
        "store_type": selected_store_types,
        "store_ids": selected_store_ids,
        "dept_ids": selected_dept_ids,
    }