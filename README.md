# Credit Card Transactions Analytics — Issuer QBR Simulation

> A SQL + dashboard project simulating the analytics an associate on a
> financial institution partnership team would deliver in a Quarterly
> Business Review (QBR) for a card-issuing bank.

## Overview
<!-- 1 short paragraph: who this is for, what business question it answers,
     why it matters to an issuer/bank partnership team. -->

## Tech Stack
- **SQL / Warehouse:** Google BigQuery (free tier)
- **Dashboard:** Looker Studio
- **Data prep:** Python (pandas)
- **Source control:** Git / GitHub

## Data
- Source: IBM Synthetic Credit Card Transactions (Kaggle)
- Volume: ~24M transactions across users, cards, and merchants
- See [`data/README.md`](data/README.md) for download and load steps.

## Repo Structure
```
credit-card-analytics/
├── sql/              # Analysis queries grouped by QBR theme
├── data/             # Raw + processed data (gitignored)
├── notebooks/        # Loading / EDA notebooks
├── dashboards/       # Looker Studio link + screenshots
└── docs/             # Methodology, KPI definitions
```

## KPIs Tracked
Grouped to mirror a real issuer QBR deck:
- **Portfolio Health** — volume, active card rate, avg ticket, MoM/YoY growth
- **Merchant & Category** — top categories, mix shift, avg ticket by MCC
- **Customer Behavior** — cohort retention, spender concentration, multi-card usage
- **Risk & Ops** — decline rate, fraud signals, geographic concentration

## Dashboard
- **Live link:** _TBD — Looker Studio URL_
- **Screenshots:** [`dashboards/screenshots/`](dashboards/screenshots/)

## Key Findings
<!-- Fill in after running queries. 5–7 bullets with actual numbers.
     Frame each as a business insight, not a SQL result.
     Example shape: "Grocery spend grew X% MoM in Q3 while active card
     rate held flat — suggests basket expansion, not new acquisition." -->
- [ ] Finding 1
- [ ] Finding 2
- [ ] Finding 3
- [ ] Finding 4
- [ ] Finding 5

## Methodology
See [`docs/methodology.md`](docs/methodology.md) for assumptions, sampling
approach, and KPI definitions.

## What I'd Do Next
<!-- Fill in: e.g., add a merchant attrition model, layer in interchange-
     revenue estimates, build a decline-reason classifier, etc. -->

## About
Built by [your name] as a portfolio project targeting FinTech / payments
analyst roles. [LinkedIn] · [Email]
