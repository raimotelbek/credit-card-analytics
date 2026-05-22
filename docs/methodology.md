# Methodology

## KPI Definitions

- **Approved Volume.** `SUM(amount) WHERE NOT declined`. A transaction
  is "declined" when its `errors` field is non-empty (any value in the
  IBM `errors` column is treated as a decline reason).
- **Tx Count.** `COUNT(*)` of attempted transactions.
- **Active Card.** A card with >=1 approved transaction in the period.
- **Eligible Card.** A card whose `issue_date` <= end of the month and
  whose `expires` >= start of the month (i.e., it could have been used).
- **Active Card Rate.** Active cards / eligible cards. Reported monthly.
- **Avg Ticket.** Approved volume / approved tx count.
- **MoM / YoY Growth.** Standard period-over-period: window function
  `LAG(volume, 1)` and `LAG(volume, 12)`.
- **Decline Rate.** Declines / attempts in the period.
- **Cohort.** Users grouped by `DATE_TRUNC(signup_date, MONTH)`. Cohort
  *size* is the full count of users who signed up that month (whether
  they ever transacted or not), so retention can never exceed 100%.
- **Spender Decile.** `NTILE(10) OVER (ORDER BY total_spend DESC)` over
  user-level lifetime approved spend.

## Assumptions

- Synthetic IBM-style data; not representative of any real issuer
  portfolio. The schema matches the Kaggle dataset exactly, so swapping
  in the real file requires no query changes.
- Currency is assumed USD throughout.
- Declines are inferred from the `errors` column being non-empty. The
  raw IBM data uses the same convention.
- Fraud is taken at face value from the `is_fraud` flag (Yes/No).

## Sampling

The 500K-row dataset is small enough to load whole to both DuckDB and
BigQuery free tier. If you swap in the full ~24M-row Kaggle file and
need to stay inside the 1 TB free monthly scan quota:

- **Sample by `user_id`, not by row.** Hashing rows breaks cohort logic
  because individual users will appear / disappear mid-history. Sample
  e.g. 10% of `user_id`s and keep all of those users' transactions.
- BigQuery: `WHERE MOD(FARM_FINGERPRINT(CAST(user_id AS STRING)), 10) = 0`.

## BigQuery / DuckDB dialect notes

Every SQL file in `/sql` is written in BigQuery dialect and tested
locally against DuckDB by `python/run_queries.py`, which performs three
small substitutions at run time:

| BigQuery                                  | DuckDB equivalent                          |
|-------------------------------------------|--------------------------------------------|
| `DATE_TRUNC(col, MONTH)`                  | `DATE_TRUNC('month', col)`                 |
| `DATE_DIFF(end, start, MONTH)`            | `DATE_DIFF('month', start, end)`           |
| `APPROX_QUANTILES(c, 100)[OFFSET(50)]`    | `QUANTILE_CONT(c, 0.5)`                    |

`QUALIFY`, `LAST_DAY`, `NTILE`, `LAG`, `RANK`, `SUM(..) OVER (..)`, and
named-window CTEs work identically in both engines, so the queries
otherwise port directly.

## Why DuckDB for local testing

It speaks SQL very close to BigQuery, runs against the same Parquet/CSV
files, and is free + offline. We get a tight local feedback loop on
every query (<=1s per query against 500K rows) before paying for
BigQuery slot time. The wins:

1. Every query in `/sql` is regression-tested before it lands.
2. Reviewers without GCP credentials can still reproduce results.
3. The `run_queries.py` summary table acts as a smoke test — if a
   query starts returning the wrong row count after an edit, it's
   visible immediately.
