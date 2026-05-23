# Looker Studio Build Guide

Step-by-step to recreate the dashboard from the SQL in [`/sql`](../sql/).
Each tile names its source query so a reviewer can trace any number on
the dashboard back to the SQL that produced it.

Mockup: [`mockup.png`](mockup.png).

---

## 0. Data source

Point Looker Studio at the BigQuery dataset `credit_card_analytics`
loaded via [`python/duckdb_to_bigquery.py`](../python/duckdb_to_bigquery.py).
Create five **custom queries** as the data sources — one per dashboard
section — using the SQL from `/sql`. Custom queries (vs. raw tables)
push aggregation to BigQuery and keep the dashboard fast.

| Looker data source | SQL file | Section it powers |
|---|---|---|
| `ds_portfolio_health`  | `01_portfolio_health.sql`  (Q1.1) | KPI strip + volume trend |
| `ds_active_rate`       | `01_portfolio_health.sql`  (Q1.2) | Active card rate gauge |
| `ds_category_share`    | `02_merchant_category.sql` (Q2.1, Q2.2) | Category mix |
| `ds_cohort_retention`  | `03_customer_behavior.sql` (Q3.1) | Cohort heatmap |
| `ds_geo`               | `04_risk_operations.sql`   (Q4.3) | Geo concentration map |

---

## 1. Page layout

One landing page, six rows:

```
┌──────────────────────────────────────────────────────────────────────┐
│  TITLE: Issuer Portfolio QBR · 2025 H1                               │
│  FILTERS:  [date range]  [card_brand]  [merchant_state]              │
├──────────────────────────────────────────────────────────────────────┤
│  [ Total Volume ] [ Tx Count ] [ Active Cards ] [ Avg Ticket ]       │  ← Row 1: KPI scorecards
│  [ Active Rate ] [ MoM Growth ]                                      │
├──────────────────────────────────────────────────────────────────────┤
│  Monthly approved volume (line)        │ Category mix (stacked area) │  ← Row 2: trends
├──────────────────────────────────────────────────────────────────────┤
│  Top 10 categories (bar)               │ Top merchants (table)       │  ← Row 3: rankings
├──────────────────────────────────────────────────────────────────────┤
│  Cohort retention (heatmap)            │ Spender concentration (bar) │  ← Row 4: customers
├──────────────────────────────────────────────────────────────────────┤
│  Geographic volume (US map)            │ Decline & fraud (table)     │  ← Row 5: risk
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tile-by-tile configuration

### Row 1 — KPI scorecards

| Tile | Type | Source | Field | Comparison | Notes |
|---|---|---|---|---|---|
| Total Volume       | Scorecard | `ds_portfolio_health` | `SUM(approved_volume_usd)` | vs. prior period | `$#,###` format |
| Tx Count           | Scorecard | `ds_portfolio_health` | `SUM(tx_count)`            | vs. prior period | `#,###` |
| Active Cards       | Scorecard | `ds_portfolio_health` | `MAX(active_cards)`        | vs. prior period | latest-period value |
| Avg Ticket         | Scorecard | `ds_portfolio_health` | `AVG(avg_ticket_usd)`      | vs. prior period | `$#.##` |
| Active Rate        | Scorecard | `ds_active_rate`      | `AVG(active_rate_pct)`     | vs. prior period | `#.#%` |
| MoM Growth         | Scorecard | `ds_portfolio_health` | computed from Q1.4         | n/a              | manual KPI from Q1.4 |

### Row 2 — Trends

**Monthly approved volume — line chart**
- Source: `ds_portfolio_health`
- Dimension: `month`
- Metric: `approved_volume_usd`
- Secondary metric (right axis): `active_cards`
- Add a 3-month moving-average reference line (use Looker's "Optional metrics" trend line)

**Category mix — 100% stacked area**
- Source: `ds_category_share` (Q2.2)
- Dimension: `month`
- Breakdown dimension: `category`
- Metric: `pct_of_month`
- Limit to top 10 categories (apply filter `category IN (...top 10 from Q2.1...)`)

### Row 3 — Rankings

**Top 10 categories — horizontal bar chart**
- Source: `ds_category_share` (Q2.1)
- Dimension: `category`
- Metric: `approved_volume_usd`
- Secondary metric: `pct_of_portfolio` (shown as data label)
- Sort: metric descending

**Top merchants in #1 category — table**
- Source: custom query of Q2.4
- Columns: `merchant_rank`, `merchant_name`, `approved_volume_usd`, `tx_count`, `unique_cards`
- Row banding on; conditional formatting on `approved_volume_usd`

### Row 4 — Customer behavior

**Cohort retention heatmap**
- Source: `ds_cohort_retention` (Q3.1)
- Pivot rows: `cohort_month`
- Pivot cols: `months_since_signup`
- Metric: `retention_pct`
- Heatmap color scale: 0% → red, 50% → yellow, 100% → green

**Spender concentration — horizontal bar**
- Source: custom query of Q3.2
- Dimension: `spender_tier`
- Metric: `pct_of_total_spend`
- Optional second metric on data labels: `avg_spend_per_user_usd`

### Row 5 — Risk

**Geographic volume — filled US map (geo chart)**
- Source: `ds_geo` (Q4.3)
- Geo dimension: `state` (set as Region → US state)
- Metric: `approved_volume_usd`
- Tooltip: `pct_of_portfolio`, `unique_users`

**Decline & fraud — table**
- Source: custom query of Q4.2
- Columns: `category`, `use_chip`, `fraud_rate_pct`, `fraud_volume_usd`
- Row-level color on `fraud_rate_pct` > 1%

---

## 3. Filters / controls (top of page)

1. **Date range** — applies to every chart (set up Looker's date control with default = "Last 12 months").
2. **Card brand** — multi-select filter on `card_brand` (requires joining cards in custom queries that don't already include it).
3. **Merchant state** — multi-select on `merchant_state`.

---

## 4. Publishing checklist

- [ ] Custom queries saved with descriptive labels (`ds_portfolio_health`, etc.).
- [ ] Date control wired up; default last-12-months.
- [ ] All currency fields formatted `$#,###` and rates `#.##%`.
- [ ] Tile titles match the section names above so the dashboard reads as
      a QBR deck (not a generic BI dashboard).
- [ ] Share link set to "Anyone with the link can view".
- [ ] Drop the live URL into [`README.md`](../README.md) and
      `dashboards/README.md`.
