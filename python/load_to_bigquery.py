"""Load the cleaned transactions/users/cards tables into BigQuery.

Run after `clean_and_load.py` has produced the local DuckDB warehouse,
or directly off the raw CSVs. Assumes GOOGLE_APPLICATION_CREDENTIALS is
set and a dataset named `credit_card_analytics` exists in your project.

Free tier note: BigQuery free tier gives 10 GB storage + 1 TB query
scan/month. The 500K-row sample fits easily; the full 24M-row IBM file
also fits in storage but you'll want to use partitioned tables and
clustered keys (already configured below) to stay under the scan quota.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

PROJECT = os.environ.get("GCP_PROJECT", "your-gcp-project")
DATASET = os.environ.get("BQ_DATASET", "credit_card_analytics")


SCHEMA_TX = [
    bigquery.SchemaField("user_id", "INT64"),
    bigquery.SchemaField("card_id", "INT64"),
    bigquery.SchemaField("tx_date", "DATE"),
    bigquery.SchemaField("year", "INT64"),
    bigquery.SchemaField("month", "INT64"),
    bigquery.SchemaField("day", "INT64"),
    bigquery.SchemaField("time", "STRING"),
    bigquery.SchemaField("amount", "FLOAT64"),
    bigquery.SchemaField("use_chip", "STRING"),
    bigquery.SchemaField("merchant_name", "STRING"),
    bigquery.SchemaField("merchant_city", "STRING"),
    bigquery.SchemaField("merchant_state", "STRING"),
    bigquery.SchemaField("zip", "STRING"),
    bigquery.SchemaField("mcc", "INT64"),
    bigquery.SchemaField("errors", "STRING"),
    bigquery.SchemaField("is_fraud", "BOOL"),
    bigquery.SchemaField("declined", "BOOL"),
]


def main() -> None:
    client = bigquery.Client(project=PROJECT)

    # transactions — partitioned by tx_date, clustered by mcc + merchant_state
    table_id = f"{PROJECT}.{DATASET}.transactions"
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA_TX,
        write_disposition="WRITE_TRUNCATE",
        time_partitioning=bigquery.TimePartitioning(field="tx_date"),
        clustering_fields=["mcc", "merchant_state"],
    )

    tx = pd.read_csv(RAW / "transactions.csv")
    tx["amount"] = tx["amount"].astype(str).str.replace("$", "", regex=False).astype(float)
    tx["tx_date"] = pd.to_datetime(dict(year=tx["year"], month=tx["month"], day=tx["day"])).dt.date
    tx["is_fraud"] = tx["is_fraud"].str.lower().eq("yes")
    tx["declined"] = tx["errors"].fillna("").str.len().gt(0)
    tx["errors"] = tx["errors"].fillna("")

    job = client.load_table_from_dataframe(tx, table_id, job_config=job_config)
    job.result()
    print(f"loaded {tx.shape[0]:,} rows into {table_id}")

    # users + cards — small, no partitioning needed
    users = pd.read_csv(RAW / "users.csv", parse_dates=["signup_date"])
    cards = pd.read_csv(RAW / "cards.csv", parse_dates=["issue_date", "expires"])
    cards["has_chip"] = cards["has_chip"].str.upper().eq("YES")

    for name, df in [("users", users), ("cards", cards)]:
        tid = f"{PROJECT}.{DATASET}.{name}"
        cfg = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
        client.load_table_from_dataframe(df, tid, job_config=cfg).result()
        print(f"loaded {len(df):,} rows into {tid}")


if __name__ == "__main__":
    main()
