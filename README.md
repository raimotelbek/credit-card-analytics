# Credit Card Transactions Analytics — Issuer QBR Simulation

> A SQL + dashboard project simulating the analytics an analyst on a
> financial institution partnership team would deliver in a Quarterly
> Business Review (QBR) for a card-issuing bank. Built to showcase the
> SQL, KPI design, and storytelling skills needed for FinTech / payments
> analyst roles.

![Dashboard mockup](dashboards/mockup.png)

## Overview

The project takes an issuer's transaction-level data and turns it into
a single read-out an account team can walk into a partner meeting with:
how is the portfolio growing, where is spend concentrated, which users
matter most, and what risks are worth flagging. The four query themes
(portfolio health, merchant/category insights, customer behavior, risk
& operations) match the structure of a real-world issuer QBR deck.

## Tech Stack

- **SQL / Warehouse:** Google BigQuery (free tier) — partitioned and
  clustered tables to stay under scan quotas
- **Dashboard:** Looker Studio (custom queries -> 6-section dashboard)
- **Data prep:** Python 3 + pandas
- **Local testing:** DuckDB — the same SQL runs locally so every query
  in `/sql` is regression-tested against real numbers before pushing
- **Source control:** Git / GitHub

## Data

- **Source:** [IBM Credit Card Transactions on Kaggle](https://www.kaggle.com/datasets/ealtman2019/credit-card-transactions)
  (Ealtman 2019). The findings in this repo were generated against the
  **real dataset**: 24.4M transactions, 2,000 cardholders, 6,146 cards,
  Jan 1991 – Feb 2020.
- **Analysis window.** The IBM dataset accumulates synthetic-user
  activity over 29 years rather than reflecting a stable production
  portfolio. KPI-driven findings focus on the **trailing 24 months
  (Mar 2018 – Feb 2020)** as the relevant window for QBR-style
  reporting; longer-term charts are shown for context only.
- **Fallback:** [`python/generate_data.py`](python/generate_data.py)
  produces a schema-identical synthetic dataset (500K rows) for use
  when Kaggle isn't available — useful for CI / quick iteration.
- **Schema:** `transactions(user_id, card_id, year, month, day, time,
  amount, use_chip, merchant_name, merchant_city, merchant_state, zip,
  mcc, errors, is_fraud)` plus `users` and `cards` tables.
- See [`data/README.md`](data/README.md) for download/load notes.

## Repo Structure

```
credit-card-analytics/
├── sql/                Analysis queries grouped by QBR theme (15 total)
├── python/             Data generation, cleaning, BigQuery + DuckDB loaders
├── data/               Raw + processed CSVs (raw gitignored)
├── dashboards/         Looker Studio build guide + PNG mockup
└── docs/               Findings writeup + methodology
```

## KPIs Tracked

Grouped to mirror a real issuer QBR deck:

- **Portfolio Health** — monthly volume, active card rate, avg ticket,
  MoM / YoY growth ([`sql/01_portfolio_health.sql`](sql/01_portfolio_health.sql))
- **Merchant & Category** — top categories, mix shift, avg ticket by
  MCC, top merchants in #1 category ([`sql/02_merchant_category.sql`](sql/02_merchant_category.sql))
- **Customer Behavior** — cohort retention, spender concentration,
  multi-card usage, per-active-user engagement ([`sql/03_customer_behavior.sql`](sql/03_customer_behavior.sql))
- **Risk & Ops** — decline rate by category and time, fraud rate by
  category and channel, geographic concentration ([`sql/04_risk_operations.sql`](sql/04_risk_operations.sql))

## Key Findings

Full writeup with numbers and recommended next steps:
**[`docs/findings.md`](docs/findings.md)**. Headlines:

1. Portfolio closed 2019 at a **$72M annualized run-rate** and Jan 2020
   was up **+16% YoY** — strong momentum into the new year.
2. **Active-card rate is at ceiling (~100%)** — future growth has to
   come from per-card spend, not from activating dormant plastic.
3. **Money Transfer is the surprise #1 category** at 10.4% of spend —
   under-monetized vs. its volume rank.
4. **Top 10% of users drive 31.7% of volume**; bottom 50% drive 15.4%.
5. **Multi-card users spend ~3x single-card users** ($822K vs $265K
   lifetime).
6. Top-5-state concentration is 38.6% — well-diversified.
7. **Fraud is concentrated in online-channel** card-not-present
   transactions; in-person chip fraud is <0.1%.
8. Per-active-user engagement is exceptional (~90 tx/month) and
   already saturated — invest in acquisition and retention, not
   engagement campaigns.

## Dashboard

The dashboard is delivered as a rendered PNG built directly from the
real BigQuery query outputs, plus a Looker Studio build guide.

- **Visual:** [`dashboards/mockup.png`](dashboards/mockup.png) — the
  image at the top of this README. Numbers and trends are real, pulled
  from `data/processed/query_outputs/`.
- **Looker Studio build guide:** [`dashboards/BUILD_GUIDE.md`](dashboards/BUILD_GUIDE.md)
  — tile-by-tile configuration mapping each chart to the SQL query that
  feeds it. The dataset is already loaded into BigQuery
  (`credit-card-analytics-497117.credit_card_analytics`), so a Looker
  Studio reviewer can point a report at it and rebuild the dashboard
  in ~30 minutes.

## How to Reproduce

```bash
# 1. clone + venv
git clone <this repo> && cd credit-card-analytics
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. get data
#    real:       python python/download_kaggle.py
#    synthetic:  python python/generate_data.py    # 500K rows, ~10s

# 3. clean + load to local DuckDB warehouse
python python/clean_and_load.py

# 4. run every SQL file and save outputs to data/processed/query_outputs/
python python/run_queries.py

# 5. render the dashboard mockup PNG
python python/build_mockup.py
```

Loading to BigQuery (after running the local pipeline above):

```bash
# 1. create the BigQuery dataset (one-time)
bq mk --location=US --dataset your-project:credit_card_analytics

# 2. export DuckDB tables to Parquet and load to BigQuery
#    (partitioned monthly by tx_date, clustered on mcc + merchant_state)
export GCP_PROJECT=your-project
python python/duckdb_to_bigquery.py
```

The dataset for this project is live at
`credit-card-analytics-497117.credit_card_analytics` (BigQuery):
24,386,900 rows in `transactions` (monthly-partitioned by `tx_date`,
clustered on `mcc, merchant_state`), 2,000 in `users`, 6,146 in
`cards`, 64 in `mcc_lookup`. Verified via `bq query`.

## What I'd Do Next

- **Layer in interchange revenue** at the MCC level so the team can
  rank categories by contribution margin, not just gross volume.
- **Build a churn-risk model** on the top decile of spenders
  (multi-card, drop in monthly transactions, category drift) and route
  flagged users to retention.
- **Connect to dbt** — turn the four SQL files into a small dbt project
  with tests on row counts, primary-key uniqueness, and KPI drift.
- **Add a decline-reason classifier** — group raw `errors` strings into
  ~6 actionable buckets (auth, network, balance, fraud-rule) so the ops
  team can prioritize fixes.

## Methodology

See [`docs/methodology.md`](docs/methodology.md) for KPI definitions,
sampling approach, and the BigQuery / DuckDB dialect notes used so the
same SQL file runs against both engines.

