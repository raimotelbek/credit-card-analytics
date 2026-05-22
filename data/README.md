# Data

Raw data is **not committed** to this repo (file size + Kaggle license).
This file documents how to obtain and load it.

## Source

IBM Synthetic Credit Card Transactions — available on Kaggle. Search:
`credit card transactions dataset IBM`. The dataset has been re-uploaded
under several owners; [`../python/download_kaggle.py`](../python/download_kaggle.py)
tries the common slugs.

Three core files (names may vary by uploader):

- `transactions.csv` — ~24M rows of card transactions
- `users.csv` — user demographics
- `cards.csv` — card-level attributes

## Synthetic fallback

If the Kaggle download fails or you'd rather skip the 24M-row pull,
[`../python/generate_data.py`](../python/generate_data.py) produces a
**schema-identical synthetic dataset** (500K transactions, 5K users,
~8K cards, 36 months) in roughly 10 seconds. Every query in `/sql`
ran against this synthetic dataset to produce the numbers in
[`../docs/findings.md`](../docs/findings.md).

## Layout

```
data/
├── raw/                          # original Kaggle CSVs (gitignored)
│   ├── transactions.csv
│   ├── users.csv
│   └── cards.csv
├── processed/                    # committed: small samples for reviewers
│   ├── transactions_sample.csv   # 10K-row sample
│   ├── users_sample.csv          # 500-row sample
│   ├── cards_sample.csv          # 1K-row sample
│   └── query_outputs/            # gitignored: full CSV results
└── warehouse.duckdb              # local DuckDB warehouse (gitignored)
```

## Loading

```bash
# generates a clean local DuckDB warehouse with three tables:
#   analytics.transactions, analytics.users, analytics.cards
# plus analytics.mcc_lookup for human-readable MCC names.
python python/clean_and_load.py
```

See [`../docs/methodology.md`](../docs/methodology.md) for KPI
definitions and the BigQuery <-> DuckDB dialect notes.
