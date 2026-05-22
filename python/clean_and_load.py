"""Clean raw IBM-schema CSVs and load them into a local DuckDB database
for testing the BigQuery SQL. Also writes a small representative sample
to data/processed/ for the repo.

Why DuckDB: it speaks SQL very close to BigQuery (window funcs, CTEs,
DATE_TRUNC, QUALIFY) so the same queries that pass locally will run on
BigQuery with at most trivial dialect tweaks (documented in
docs/methodology.md).
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "data" / "warehouse.duckdb"


def load_transactions() -> pd.DataFrame:
    df = pd.read_csv(RAW / "transactions.csv")
    # IBM amount is "$12.34" — strip $ and cast
    df["amount"] = df["amount"].astype(str).str.replace("$", "", regex=False).astype(float)
    # combine year/month/day into a real DATE
    df["tx_date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=df["day"]))
    df["is_fraud"] = df["is_fraud"].str.lower().eq("yes")
    df["declined"] = df["errors"].fillna("").str.len().gt(0)
    df["mcc"] = df["mcc"].astype(int)
    # null normalization
    df["errors"] = df["errors"].fillna("")
    return df


def load_users() -> pd.DataFrame:
    df = pd.read_csv(RAW / "users.csv", parse_dates=["signup_date"])
    return df


def load_cards() -> pd.DataFrame:
    df = pd.read_csv(RAW / "cards.csv", parse_dates=["issue_date", "expires"])
    df["has_chip"] = df["has_chip"].str.upper().eq("YES")
    return df


def main() -> None:
    print("reading raw CSVs...")
    tx = load_transactions()
    users = load_users()
    cards = load_cards()
    print(f"  transactions: {len(tx):,}")
    print(f"  users:        {len(users):,}")
    print(f"  cards:        {len(cards):,}")

    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

    con.register("tx_df", tx)
    con.register("users_df", users)
    con.register("cards_df", cards)

    con.execute("""
        CREATE OR REPLACE TABLE analytics.transactions AS
        SELECT
            CAST(user_id AS INTEGER)       AS user_id,
            CAST(card_id AS INTEGER)       AS card_id,
            CAST(tx_date AS DATE)          AS tx_date,
            CAST(year   AS INTEGER)        AS year,
            CAST(month  AS INTEGER)        AS month,
            CAST(day    AS INTEGER)        AS day,
            CAST(time   AS VARCHAR)        AS time,
            CAST(amount AS DOUBLE)         AS amount,
            CAST(use_chip AS VARCHAR)      AS use_chip,
            CAST(merchant_name  AS VARCHAR) AS merchant_name,
            CAST(merchant_city  AS VARCHAR) AS merchant_city,
            CAST(merchant_state AS VARCHAR) AS merchant_state,
            CAST(zip AS VARCHAR)           AS zip,
            CAST(mcc AS INTEGER)           AS mcc,
            CAST(errors AS VARCHAR)        AS errors,
            CAST(is_fraud AS BOOLEAN)      AS is_fraud,
            CAST(declined AS BOOLEAN)      AS declined
        FROM tx_df;
    """)
    con.execute("""
        CREATE OR REPLACE TABLE analytics.users AS
        SELECT
            CAST(user_id AS INTEGER)       AS user_id,
            CAST(signup_date AS DATE)      AS signup_date,
            CAST(birth_year AS INTEGER)    AS birth_year,
            CAST(gender AS VARCHAR)        AS gender,
            CAST(state AS VARCHAR)         AS state,
            CAST(yearly_income AS INTEGER) AS yearly_income,
            CAST(credit_score AS INTEGER)  AS credit_score
        FROM users_df;
    """)
    con.execute("""
        CREATE OR REPLACE TABLE analytics.cards AS
        SELECT
            CAST(card_id AS INTEGER)   AS card_id,
            CAST(user_id AS INTEGER)   AS user_id,
            CAST(card_brand AS VARCHAR) AS card_brand,
            CAST(card_type  AS VARCHAR) AS card_type,
            CAST(issue_date AS DATE)   AS issue_date,
            CAST(expires    AS DATE)   AS expires,
            CAST(has_chip   AS BOOLEAN) AS has_chip
        FROM cards_df;
    """)

    # MCC lookup table — handy for joining human-readable category names.
    mcc_rows = [
        (5411, "Grocery Stores"), (5812, "Restaurants"), (5814, "Fast Food"),
        (5541, "Gas Stations"), (5311, "Department Stores"), (5912, "Drug Stores"),
        (5942, "Bookstores"), (5732, "Electronics"), (5651, "Apparel"),
        (4111, "Transit"), (4121, "Taxis/Rideshare"), (4511, "Airlines"),
        (7011, "Hotels"), (5999, "Misc Retail"), (5921, "Liquor Stores"),
        (7832, "Movie Theaters"), (7997, "Gyms/Clubs"),
        (5734, "Software/Subscriptions"), (8011, "Medical/Doctors"),
        (5200, "Home Improvement"),
    ]
    con.execute("CREATE OR REPLACE TABLE analytics.mcc_lookup (mcc INTEGER, category VARCHAR);")
    con.executemany("INSERT INTO analytics.mcc_lookup VALUES (?, ?);", mcc_rows)

    # Small sample for the repo so reviewers can poke at structure.
    print("writing committed sample (10K tx)...")
    sample = tx.sample(10_000, random_state=42).sort_values("tx_date")
    sample.to_csv(PROC / "transactions_sample.csv", index=False)
    users.head(500).to_csv(PROC / "users_sample.csv", index=False)
    cards.head(1000).to_csv(PROC / "cards_sample.csv", index=False)

    con.close()
    print(f"loaded into {DB_PATH}")


if __name__ == "__main__":
    main()
