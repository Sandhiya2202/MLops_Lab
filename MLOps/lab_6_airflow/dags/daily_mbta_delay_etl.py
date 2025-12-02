from datetime import datetime, timedelta
import json
import os

import pandas as pd
import requests
import urllib3

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.exceptions import AirflowFailException

# Disable SSL warnings (useful inside Docker on Mac)
urllib3.disable_warnings()

# Directory inside the Airflow container
DATA_DIR = "/opt/airflow/data"

# Base MBTA Commuter Rail predictions endpoint
# Use a specific commuter rail route (CR-Fitchburg) so the filter is valid
MBTA_PREDICTIONS_URL = (
    "https://api-v3.mbta.com/predictions"
    "?filter[route]=CR-Fitchburg"
    "&include=route,trip"
)


default_args = {
    "owner": "student",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="daily_mbta_delay_etl",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="0 6 * * *",  # run every day at 06:00
    catchup=False,
    description="Daily ETL: MBTA Commuter Rail delays snapshot",
) as dag:

    start = EmptyOperator(task_id="start")

    # -----------------------------
    # 1) Check MBTA API is reachable
    # -----------------------------
    @task
    def check_mbta_api():
        headers = {"User-Agent": "airflow-mbta-delay-etl-lab"}

        try:
            resp = requests.get(
                MBTA_PREDICTIONS_URL + "&page[limit]=5",
                headers=headers,
                timeout=15,
                verify=False,  # ignore SSL certificate issues inside Docker
            )
        except Exception as e:
            raise AirflowFailException(f"Error calling MBTA API: {e}")

        if resp.status_code != 200:
            raise AirflowFailException(
                f"MBTA API not available. Status code: {resp.status_code}"
            )

        return True

    # -----------------------------
    # 2) Extract raw predictions
    # -----------------------------
    @task
    def extract_mbta_predictions(execution_date=None):
        os.makedirs(f"{DATA_DIR}/raw", exist_ok=True)

        headers = {"User-Agent": "airflow-mbta-delay-etl-lab"}

        try:
            resp = requests.get(
                MBTA_PREDICTIONS_URL + "&page[limit]=500",
                headers=headers,
                timeout=30,
                verify=False,  # ignore SSL certificate issues inside Docker
            )
        except Exception as e:
            raise AirflowFailException(f"Error fetching MBTA predictions: {e}")

        if resp.status_code != 200:
            raise AirflowFailException(
                f"Failed to fetch MBTA predictions. Status code: {resp.status_code}"
            )

        payload = resp.json()

        raw_path = f"{DATA_DIR}/raw/mbta_predictions_{execution_date}.json"
        with open(raw_path, "w") as f:
            json.dump(payload, f)

        return raw_path

    # -----------------------------
    # 3) Transform JSON → clean CSV
    # -----------------------------
    @task
    def transform_mbta_data(raw_path: str, execution_date=None):
        os.makedirs(f"{DATA_DIR}/clean", exist_ok=True)

        with open(raw_path, "r") as f:
            payload = json.load(f)

        data = payload.get("data", [])
        included = payload.get("included", [])

        # Build lookup tables for routes and trips
        route_lookup = {}
        trip_lookup = {}

        for item in included:
            item_type = item.get("type")
            item_id = item.get("id")
            attrs = item.get("attributes", {}) or {}

            if item_type == "route":
                route_lookup[item_id] = {
                    "route_id": item_id,
                    "route_name": attrs.get("long_name") or attrs.get("short_name"),
                }
            elif item_type == "trip":
                trip_lookup[item_id] = {
                    "trip_id": item_id,
                    "direction_id": attrs.get("direction_id"),
                    "headsign": attrs.get("headsign"),
                }

        rows = []

        for pred in data:
            attrs = pred.get("attributes", {}) or {}
            rel = pred.get("relationships", {}) or {}

            route_rel = rel.get("route", {}) or {}
            trip_rel = rel.get("trip", {}) or {}

            route_id = (route_rel.get("data") or {}).get("id")
            trip_id = (trip_rel.get("data") or {}).get("id")

            delay_seconds = attrs.get("delay")
            departure_time = attrs.get("departure_time")
            status = attrs.get("status")

            route_info = route_lookup.get(route_id, {})
            trip_info = trip_lookup.get(trip_id, {})

            rows.append(
                {
                    "route_id": route_id,
                    "route_name": route_info.get("route_name"),
                    "trip_id": trip_id,
                    "headsign": trip_info.get("headsign"),
                    "direction_id": trip_info.get("direction_id"),
                    "status": status,
                    "delay_seconds": delay_seconds,
                    "delay_minutes": (delay_seconds / 60.0)
                    if delay_seconds is not None
                    else None,
                    "departure_time": departure_time,
                    "execution_date": execution_date,
                }
            )

        df = pd.DataFrame(rows)

        # Keep only rows where delay exists
        if not df.empty:
            df = df[df["delay_seconds"].notna()]

        clean_path = f"{DATA_DIR}/clean/mbta_delays_{execution_date}.csv"
        df.to_csv(clean_path, index=False)

        return clean_path

    # -----------------------------
    # 4) Load into "warehouse" CSV
    # -----------------------------
    @task
    def load_mbta_to_warehouse(clean_path: str):
        warehouse_path = f"{DATA_DIR}/mbta_delay_warehouse.csv"

        df_clean = pd.read_csv(clean_path)

        # Number of delayed trips in this run
        loaded_rows = len(df_clean)

        if os.path.exists(warehouse_path):
            df_existing = pd.read_csv(warehouse_path)
            df_all = pd.concat([df_existing, df_clean], ignore_index=True)
        else:
            df_all = df_clean

        df_all.to_csv(warehouse_path, index=False)

        return loaded_rows

    # -----------------------------
    # 5) Data quality check
    # -----------------------------
    @task
    def mbta_data_quality_check(loaded_rows: int):
    	"""
    	Soft data quality check:
    	- If there are delayed trips, log a success message.
   	 - If there are no delayed trips, log a warning but DO NOT fail the DAG.
    	"""
    	if loaded_rows <= 0:
        	print(
            	"Data quality check: no delayed trips were loaded for this run. "
            	"This may simply mean there were no delays at this time."
        	)
    	else:
        	print(
            	f"Data quality check passed. Delayed trips loaded: {loaded_rows}"
        	)


    end = EmptyOperator(task_id="end")

    # DAG dependencies
    api_ok = check_mbta_api()
    raw = extract_mbta_predictions()
    clean = transform_mbta_data(raw)
    loaded_rows = load_mbta_to_warehouse(clean)
    dq = mbta_data_quality_check(loaded_rows)

    start >> api_ok >> raw >> clean >> loaded_rows >> dq >> end



