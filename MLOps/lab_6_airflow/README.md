# Airflow MBTA Delay ETL 🚆

This project is a self-contained **Apache Airflow ETL pipeline** that pulls live data from the **MBTA v3 API** (Boston public transit), transforms it, and stores it in a simple “data warehouse” CSV.

It’s built to be used as a **lab assignment / portfolio project** showing:

- Airflow DAG design  
- Task dependencies  
- API integration  
- Simple data quality checks  
- Docker-based local setup  

---

## ✨ What the DAG Does

DAG ID: `daily_mbta_delay_etl`  
Schedule: `0 6 * * *` (every day at 06:00, disabled for lab by default – you can trigger manually)

Pipeline steps:

1. **`check_mbta_api`**  
   - Calls MBTA predictions API for a specific Commuter Rail route (`CR-Fitchburg`).  
   - Verifies the API is reachable and returns HTTP 200.  

2. **`extract_mbta_predictions`**  
   - Fetches predictions JSON from MBTA API.  
   - Saves raw JSON to:  
     `data/raw/mbta_predictions_<execution_date>.json`

3. **`transform_mbta_data`**  
   - Parses JSON, joins prediction data with route & trip metadata.  
   - Keeps important fields:  
     `route_id`, `route_name`, `trip_id`, `headsign`, `direction_id`, `status`, `delay_seconds`, `delay_minutes`, `departure_time`, `execution_date`.  
   - Filters to rows where `delay_seconds` is not `null`.  
   - Writes cleaned CSV to:  
     `data/clean/mbta_delays_<execution_date>.csv`

4. **`load_mbta_to_warehouse`**  
   - Appends each cleaned CSV into a simple warehouse file:  
     `data/mbta_delay_warehouse.csv`  
   - Returns the number of delayed trips loaded for that run.

5. **`mbta_data_quality_check`**  
   - Soft check:  
     - If `loaded_rows > 0` → logs “Data quality check passed”.  
     - If `loaded_rows == 0` → logs a warning (no delays this run), but **does not fail** the DAG.

---

## 🧱 Project Structure

```text
.
├─ dags/
│   └─ daily_mbta_delay_etl.py     # The Airflow DAG (MBTA ETL)
├─ data/
│   ├─ raw/                        # Raw JSON responses from MBTA API
│   ├─ clean/                      # Cleaned CSV snapshots
│   └─ mbta_delay_warehouse.csv    # Accumulated warehouse CSV (created at runtime)
├─ docs/
│   └─ airflow_mbta_dag_graph.png  # Screenshot of DAG (Graph view)
├─ logs/                           # Airflow logs (git-ignored)
├─ plugins/                        # Custom plugins (unused for now)
├─ docker-compose.yaml             # Airflow + Postgres + Redis stack
├─ requirements.txt                # Python dependencies used in DAGs
├─ README.md
└─ .gitignore

