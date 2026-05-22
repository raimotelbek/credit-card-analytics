-- =============================================================================
-- Theme A — Portfolio Health
-- =============================================================================
-- These four queries form the "is the portfolio growing, and how?" section
-- of an issuer QBR. They answer: how much volume are we processing, how many
-- cards are actually being used, what's the basket size doing, and what's
-- the growth trajectory.
--
-- BigQuery dialect. To run on DuckDB, the syntax is identical except for the
-- table prefix (use `analytics.transactions` locally vs. fully qualified
-- `project.dataset.transactions` on BigQuery).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1.1 — Monthly transaction volume and count
-- Business question:
--   How is total approved spend and transaction count trending month over month?
-- Output: one row per month with $ volume, tx count, and unique active cards.
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        DATE_TRUNC(tx_date, MONTH)        AS month,
        SUM(amount)                       AS gross_volume,
        SUM(CASE WHEN NOT declined THEN amount END) AS approved_volume,
        COUNT(*)                          AS tx_count,
        COUNT(DISTINCT card_id)           AS active_cards
    FROM analytics.transactions
    GROUP BY 1
)
SELECT
    month,
    ROUND(approved_volume, 2)             AS approved_volume_usd,
    tx_count,
    active_cards,
    ROUND(approved_volume / NULLIF(tx_count, 0), 2) AS avg_ticket_usd
FROM monthly
ORDER BY month;


-- -----------------------------------------------------------------------------
-- Q1.2 — Active card rate
-- Business question:
--   What share of issued cards has at least one transaction in a given month?
--   A flat-or-declining active rate while volume grows means the same cards
--   are being used harder rather than the portfolio broadening.
-- -----------------------------------------------------------------------------
WITH months AS (
    SELECT DISTINCT DATE_TRUNC(tx_date, MONTH) AS month
    FROM analytics.transactions
),
active AS (
    SELECT
        DATE_TRUNC(t.tx_date, MONTH) AS month,
        COUNT(DISTINCT t.card_id)    AS active_cards
    FROM analytics.transactions t
    WHERE NOT t.declined
    GROUP BY 1
),
eligible AS (
    -- a card is "eligible" in a month if it had been issued by then and
    -- has not yet expired
    SELECT
        m.month,
        COUNT(*) AS eligible_cards
    FROM months m
    JOIN analytics.cards c
        ON c.issue_date <= LAST_DAY(m.month)
       AND c.expires    >= m.month
    GROUP BY 1
)
SELECT
    e.month,
    e.eligible_cards,
    COALESCE(a.active_cards, 0)                                AS active_cards,
    ROUND(100.0 * COALESCE(a.active_cards, 0) / NULLIF(e.eligible_cards, 0), 2)
                                                               AS active_rate_pct
FROM eligible e
LEFT JOIN active a USING (month)
ORDER BY e.month;


-- -----------------------------------------------------------------------------
-- Q1.3 — Average ticket size trend
-- Business question:
--   Is spend-per-swipe growing (basket inflation, premium card mix), shrinking
--   (more low-value taps), or flat? Tracked as a 3-month moving average to
--   smooth weekend / month-end noise.
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        DATE_TRUNC(tx_date, MONTH) AS month,
        AVG(amount)                AS avg_ticket
    FROM analytics.transactions
    WHERE NOT declined
    GROUP BY 1
)
SELECT
    month,
    ROUND(avg_ticket, 2) AS avg_ticket_usd,
    ROUND(AVG(avg_ticket) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS avg_ticket_3mo_ma
FROM monthly
ORDER BY month;


-- -----------------------------------------------------------------------------
-- Q1.4 — MoM and YoY growth rates
-- Business question:
--   What is the month-over-month and year-over-year growth of approved spend?
--   YoY strips seasonality; MoM shows momentum.
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        DATE_TRUNC(tx_date, MONTH)                AS month,
        SUM(CASE WHEN NOT declined THEN amount END) AS approved_volume
    FROM analytics.transactions
    GROUP BY 1
),
with_lags AS (
    SELECT
        month,
        approved_volume,
        LAG(approved_volume, 1)  OVER (ORDER BY month) AS prior_month,
        LAG(approved_volume, 12) OVER (ORDER BY month) AS prior_year
    FROM monthly
)
SELECT
    month,
    ROUND(approved_volume, 2) AS approved_volume_usd,
    ROUND(100.0 * (approved_volume - prior_month) / NULLIF(prior_month, 0), 2) AS mom_growth_pct,
    ROUND(100.0 * (approved_volume - prior_year)  / NULLIF(prior_year,  0), 2) AS yoy_growth_pct
FROM with_lags
ORDER BY month;
