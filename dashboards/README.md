# Dashboard

## Live link

*(Looker Studio public URL goes here after publish.)*

## Build instructions

See [`BUILD_GUIDE.md`](BUILD_GUIDE.md) — tile-by-tile configuration
mapping each chart to the SQL file in [`../sql/`](../sql/) that feeds it.

## Mockup

![Dashboard mockup](mockup.png)

The mockup is rendered by [`../python/build_mockup.py`](../python/build_mockup.py)
from the actual query outputs in `../data/processed/query_outputs/`,
so the figures shown are real values from the loaded dataset.

## Tile -> Query map

| Section | Tile | SQL file | Query |
|---|---|---|---|
| KPIs    | Total Volume, Tx Count, Active Cards, Avg Ticket | `01_portfolio_health.sql` | Q1.1 |
| KPIs    | Active Rate                                      | `01_portfolio_health.sql` | Q1.2 |
| KPIs    | MoM / YoY Growth                                 | `01_portfolio_health.sql` | Q1.4 |
| Trends  | Monthly approved volume (line)                   | `01_portfolio_health.sql` | Q1.1 |
| Trends  | Category mix over time (stacked area)            | `02_merchant_category.sql` | Q2.2 |
| Ranks   | Top 10 categories (bar)                          | `02_merchant_category.sql` | Q2.1 |
| Ranks   | Top merchants in #1 category (table)             | `02_merchant_category.sql` | Q2.4 |
| Customer| Cohort retention (heatmap)                       | `03_customer_behavior.sql` | Q3.1 |
| Customer| Spender concentration (bar)                      | `03_customer_behavior.sql` | Q3.2 |
| Risk    | Geographic concentration (map / bar)             | `04_risk_operations.sql` | Q4.3 |
| Risk    | Decline & fraud (table)                          | `04_risk_operations.sql` | Q4.1, Q4.2 |
