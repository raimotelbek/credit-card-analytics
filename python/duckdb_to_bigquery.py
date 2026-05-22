"""Export the four DuckDB tables to Parquet, then load to BigQuery via
`bq load`. Parquet preserves types so we avoid the schema-inference
headaches that come with CSV loads of 24M rows.

Requires:
    - data/warehouse.duckdb populated by clean_and_load.py
    - gcloud + bq authenticated; project + dataset already created
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "warehouse.duckdb"
PARQUET_DIR = ROOT / "data" / "_bq_export"
PARQUET_DIR.mkdir(exist_ok=True)

PROJECT = os.environ.get("GCP_PROJECT", "credit-card-analytics-497117")
DATASET = os.environ.get("BQ_DATASET", "credit_card_analytics")

TABLES = ["transactions", "users", "cards", "mcc_lookup"]


def export_parquet() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    for t in TABLES:
        out = PARQUET_DIR / f"{t}.parquet"
        print(f"  exporting analytics.{t} -> {out.name}")
        con.execute(f"COPY analytics.{t} TO '{out}' (FORMAT PARQUET);")
    con.close()


def bq_load_table(table: str, extra: list[str] | None = None) -> None:
    parquet = PARQUET_DIR / f"{table}.parquet"
    target = f"{PROJECT}:{DATASET}.{table}"
    cmd = [
        "bq", "load",
        "--source_format=PARQUET",
        "--replace",
    ] + (extra or []) + [target, str(parquet)]
    print(f"  loading -> {target}")
    subprocess.run(cmd, check=True)


def main() -> None:
    print("export step:")
    export_parquet()

    print("\nload step:")
    # transactions: partition by tx_date, cluster on mcc + merchant_state
    bq_load_table("transactions", [
        "--time_partitioning_field=tx_date",
        "--time_partitioning_type=MONTH",
        "--clustering_fields=mcc,merchant_state",
    ])
    bq_load_table("users")
    bq_load_table("cards")
    bq_load_table("mcc_lookup")

    print("\ndone. tables live at:")
    for t in TABLES:
        print(f"  {PROJECT}.{DATASET}.{t}")


if __name__ == "__main__":
    main()
