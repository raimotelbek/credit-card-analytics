# Data

Raw data is **not committed** to this repo (file sizes + Kaggle terms).
This file documents how to obtain and load it.

## Source
IBM Synthetic Credit Card Transactions — available on Kaggle.
Search: `credit card transactions dataset IBM`.

Three core files (names may vary by uploader):
- `transactions.csv` — ~24M rows of card transactions
- `users.csv` — user demographics
- `cards.csv` — card-level attributes

## Download
Instructions live in [`../notebooks/01_load_to_bigquery.ipynb`](../notebooks/01_load_to_bigquery.ipynb)
(filled in during Step 2 of the build).

## Layout
```
data/
├── raw/         # original Kaggle CSVs (gitignored)
└── processed/   # cleaned / sampled parquet files (gitignored)
```
