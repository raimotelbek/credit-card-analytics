"""Clean the real IBM Credit Card Transactions CSVs and load them into a
local DuckDB warehouse. DuckDB reads the 2.2GB transactions file directly
via `read_csv_auto`, which is significantly faster than going through
pandas for a file of this size.

Produces:
    data/warehouse.duckdb  with tables
        analytics.transactions   (~24M rows)
        analytics.users          (2,000 rows)
        analytics.cards          (~6,100 rows)
        analytics.mcc_lookup     (most common MCC codes)

Also writes small sample CSVs to data/processed/ so reviewers can poke
at the structure without re-running the pipeline.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "data" / "warehouse.duckdb"

TX_CSV    = RAW / "credit_card_transactions-ibm_v2.csv"
USERS_CSV = RAW / "sd254_users.csv"
CARDS_CSV = RAW / "sd254_cards.csv"


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

    print(f"loading transactions from {TX_CSV.name} (~24M rows)...")
    # Real IBM columns: User, Card, Year, Month, Day, Time, Amount, Use Chip,
    # Merchant Name, Merchant City, Merchant State, Zip, MCC, Errors?, Is Fraud?
    con.execute(f"""
        CREATE OR REPLACE TABLE analytics.transactions AS
        SELECT
            CAST("User"   AS INTEGER)                                 AS user_id,
            -- IBM stores card as a 0-based per-user index. Make a globally
            -- unique card_id by combining user + card index.
            CAST("User" AS INTEGER) * 100 + CAST("Card" AS INTEGER)   AS card_id,
            MAKE_DATE(CAST("Year" AS INTEGER),
                      CAST("Month" AS INTEGER),
                      CAST("Day" AS INTEGER))                         AS tx_date,
            CAST("Year"  AS INTEGER)                                  AS year,
            CAST("Month" AS INTEGER)                                  AS month,
            CAST("Day"   AS INTEGER)                                  AS day,
            CAST("Time"  AS VARCHAR)                                  AS time,
            CAST(REPLACE("Amount", '$', '') AS DOUBLE)                AS amount,
            CAST("Use Chip" AS VARCHAR)                               AS use_chip,
            CAST("Merchant Name"  AS VARCHAR)                         AS merchant_name,
            CAST("Merchant City"  AS VARCHAR)                         AS merchant_city,
            CAST("Merchant State" AS VARCHAR)                         AS merchant_state,
            CAST("Zip" AS VARCHAR)                                    AS zip,
            CAST("MCC" AS INTEGER)                                    AS mcc,
            COALESCE("Errors?", '')                                   AS errors,
            "Is Fraud?"::BOOLEAN                                      AS is_fraud,
            (COALESCE("Errors?", '') <> '')                           AS declined
        FROM read_csv_auto('{TX_CSV}', header=true);
    """)
    n_tx = con.execute("SELECT COUNT(*) FROM analytics.transactions").fetchone()[0]
    print(f"  loaded {n_tx:,} transactions")

    print("loading users...")
    con.execute(f"""
        CREATE OR REPLACE TABLE analytics.users AS
        SELECT
            ROW_NUMBER() OVER () - 1                                   AS user_id,
            CAST("Person" AS VARCHAR)                                  AS person_name,
            CAST("Current Age" AS INTEGER)                             AS current_age,
            CAST("Birth Year" AS INTEGER)                              AS birth_year,
            CAST("Gender" AS VARCHAR)                                  AS gender,
            CAST("City" AS VARCHAR)                                    AS city,
            CAST("State" AS VARCHAR)                                   AS state,
            CAST(CAST("Zipcode" AS DOUBLE) AS INTEGER)                 AS zipcode,
            CAST(REPLACE("Yearly Income - Person", '$', '') AS INTEGER) AS yearly_income,
            CAST(REPLACE("Total Debt", '$', '') AS INTEGER)            AS total_debt,
            CAST("FICO Score" AS INTEGER)                              AS credit_score,
            CAST("Num Credit Cards" AS INTEGER)                        AS num_credit_cards
        FROM read_csv_auto('{USERS_CSV}', header=true);
    """)
    n_users = con.execute("SELECT COUNT(*) FROM analytics.users").fetchone()[0]
    print(f"  loaded {n_users:,} users")

    print("loading cards...")
    # Acct Open Date is "MM/YYYY" — parse to first of month. Expires likewise.
    con.execute(f"""
        CREATE OR REPLACE TABLE analytics.cards AS
        SELECT
            CAST("User" AS INTEGER) * 100 + CAST("CARD INDEX" AS INTEGER)  AS card_id,
            CAST("User" AS INTEGER)                                        AS user_id,
            CAST("Card Brand" AS VARCHAR)                                  AS card_brand,
            CAST("Card Type"  AS VARCHAR)                                  AS card_type,
            STRPTIME('01/' || "Acct Open Date", '%d/%m/%Y')::DATE          AS issue_date,
            STRPTIME('01/' || "Expires",        '%d/%m/%Y')::DATE          AS expires,
            "Has Chip"::BOOLEAN                                            AS has_chip,
            CAST(REPLACE("Credit Limit", '$', '') AS INTEGER)              AS credit_limit
        FROM read_csv_auto('{CARDS_CSV}', header=true);
    """)
    n_cards = con.execute("SELECT COUNT(*) FROM analytics.cards").fetchone()[0]
    print(f"  loaded {n_cards:,} cards")

    # Derive a signup_date for each user from the earliest card open date.
    # This is what we'll use for cohort retention.
    con.execute("""
        ALTER TABLE analytics.users ADD COLUMN signup_date DATE;
        UPDATE analytics.users u
        SET signup_date = sub.signup_date
        FROM (
            SELECT user_id, MIN(issue_date) AS signup_date
            FROM analytics.cards
            GROUP BY user_id
        ) sub
        WHERE u.user_id = sub.user_id;
    """)

    # MCC lookup — covers the top retail/travel categories that show up in
    # the dataset. Codes not in this table will simply be excluded from
    # category breakdowns (intentional — focuses on partnership-relevant
    # spend rather than long tail of utilities/government/etc).
    mcc_rows = [
        (4111, "Transit"), (4121, "Taxis/Rideshare"), (4411, "Cruises"),
        (4511, "Airlines"), (4722, "Travel Agencies"), (4784, "Tolls"),
        (4814, "Telecom"), (4829, "Money Transfer"), (4899, "Cable/Streaming"),
        (4900, "Utilities"), (5200, "Home Improvement"), (5211, "Lumber/Building"),
        (5300, "Wholesale Clubs"), (5311, "Department Stores"), (5411, "Grocery Stores"),
        (5499, "Misc Food Stores"), (5541, "Gas Stations"), (5651, "Apparel"),
        (5712, "Furniture"), (5722, "Appliances"), (5732, "Electronics"),
        (5812, "Restaurants"), (5813, "Bars"), (5814, "Fast Food"),
        (5912, "Drug Stores"), (5921, "Liquor Stores"), (5942, "Bookstores"),
        (5970, "Crafts"), (5977, "Cosmetics"), (5999, "Misc Retail"),
        (6300, "Insurance"), (7011, "Hotels"), (7230, "Beauty/Barber"),
        (7538, "Auto Service"), (7549, "Towing"), (7832, "Movie Theaters"),
        (7995, "Gambling"), (7997, "Gyms/Clubs"), (8011, "Medical/Doctors"),
        (8021, "Dentists"), (8062, "Hospitals"), (8099, "Health Services"),
        (5734, "Software/Subscriptions"), (5310, "Discount Stores"),
        (5193, "Florists"), (5251, "Hardware"), (3000, "Airline (other)"),
        (3001, "Airline (other)"), (3132, "Airline (other)"),
        (3144, "Airline (other)"), (3174, "Airline (other)"),
        (3256, "Airline (other)"), (3260, "Airline (other)"),
        (3387, "Car Rental"), (3389, "Car Rental"), (3393, "Car Rental"),
        (3395, "Car Rental"), (3501, "Hotels"), (3504, "Hotels"),
        (3596, "Hotels"), (3640, "Hotels"), (3684, "Hotels"),
        (3722, "Hotels"), (3771, "Hotels"),
    ]
    con.execute("CREATE OR REPLACE TABLE analytics.mcc_lookup (mcc INTEGER, category VARCHAR);")
    con.executemany("INSERT INTO analytics.mcc_lookup VALUES (?, ?);", mcc_rows)

    print("writing committed samples...")
    con.execute(f"""
        COPY (SELECT * FROM analytics.transactions
              USING SAMPLE 10000 ROWS) TO '{PROC / "transactions_sample.csv"}'
        (HEADER, DELIMITER ',');
    """)
    con.execute(f"""
        COPY (SELECT * FROM analytics.users LIMIT 500)
            TO '{PROC / "users_sample.csv"}' (HEADER, DELIMITER ',');
    """)
    con.execute(f"""
        COPY (SELECT * FROM analytics.cards LIMIT 1000)
            TO '{PROC / "cards_sample.csv"}' (HEADER, DELIMITER ',');
    """)

    yr_min, yr_max = con.execute(
        "SELECT MIN(year), MAX(year) FROM analytics.transactions"
    ).fetchone()
    print(f"  transactions span {yr_min} – {yr_max}")
    con.close()
    print(f"done. warehouse at {DB_PATH}")


if __name__ == "__main__":
    main()
