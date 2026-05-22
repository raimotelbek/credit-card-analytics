-- =============================================================================
-- Theme B — Merchant & Category Insights
-- =============================================================================
-- "Where is the money going?" — the merchant category section of a QBR.
-- Useful for partnership conversations: if grocery is 25% of spend and
-- growing 8% YoY, that informs co-brand and rewards-bonus decisions.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q2.1 — Top 10 merchant categories by approved spend
-- Business question:
--   Which categories drive the most volume? Pareto check for partnership focus.
-- -----------------------------------------------------------------------------
WITH cat_totals AS (
    SELECT
        m.category,
        SUM(t.amount)              AS approved_volume,
        COUNT(*)                   AS tx_count,
        COUNT(DISTINCT t.card_id)  AS unique_cards
    FROM analytics.transactions t
    JOIN analytics.mcc_lookup m USING (mcc)
    WHERE NOT t.declined
    GROUP BY 1
),
ranked AS (
    SELECT
        category,
        approved_volume,
        tx_count,
        unique_cards,
        SUM(approved_volume) OVER ()                          AS portfolio_volume,
        RANK() OVER (ORDER BY approved_volume DESC)           AS volume_rank
    FROM cat_totals
)
SELECT
    volume_rank,
    category,
    ROUND(approved_volume, 2)                                 AS approved_volume_usd,
    tx_count,
    unique_cards,
    ROUND(100.0 * approved_volume / portfolio_volume, 2)      AS pct_of_portfolio
FROM ranked
WHERE volume_rank <= 10
ORDER BY volume_rank;


-- -----------------------------------------------------------------------------
-- Q2.2 — Category mix shift over time
-- Business question:
--   How is the share of total monthly spend by category changing? Mix shift
--   matters more than absolute growth — a category gaining share is taking
--   wallet from another category, which is a leading indicator.
-- -----------------------------------------------------------------------------
WITH monthly_cat AS (
    SELECT
        DATE_TRUNC(t.tx_date, MONTH) AS month,
        m.category,
        SUM(t.amount)                AS approved_volume
    FROM analytics.transactions t
    JOIN analytics.mcc_lookup m USING (mcc)
    WHERE NOT t.declined
    GROUP BY 1, 2
),
monthly_totals AS (
    SELECT month, SUM(approved_volume) AS month_total
    FROM monthly_cat
    GROUP BY 1
)
SELECT
    mc.month,
    mc.category,
    ROUND(mc.approved_volume, 2)                          AS category_volume_usd,
    ROUND(100.0 * mc.approved_volume / mt.month_total, 2) AS pct_of_month
FROM monthly_cat mc
JOIN monthly_totals mt USING (month)
ORDER BY mc.month, pct_of_month DESC;


-- -----------------------------------------------------------------------------
-- Q2.3 — Average transaction size by category
-- Business question:
--   Which categories are high-ticket (airlines, hotels) vs. high-frequency
--   (transit, fast food)? Drives reward-multiplier and fraud-threshold design.
-- -----------------------------------------------------------------------------
SELECT
    m.category,
    COUNT(*)                                           AS tx_count,
    ROUND(AVG(t.amount), 2)                            AS avg_ticket_usd,
    ROUND(APPROX_QUANTILES(t.amount, 100)[OFFSET(50)], 2) AS median_ticket_usd,
    ROUND(APPROX_QUANTILES(t.amount, 100)[OFFSET(95)], 2) AS p95_ticket_usd,
    ROUND(SUM(t.amount), 2)                            AS approved_volume_usd
FROM analytics.transactions t
JOIN analytics.mcc_lookup m USING (mcc)
WHERE NOT t.declined
GROUP BY 1
ORDER BY avg_ticket_usd DESC;


-- -----------------------------------------------------------------------------
-- Q2.4 — Top merchants within the #1 category
-- Business question:
--   Inside the largest category, which individual merchants drive the spend?
--   This is the "who do we call for a co-brand" list.
-- -----------------------------------------------------------------------------
WITH top_cat AS (
    SELECT m.category
    FROM analytics.transactions t
    JOIN analytics.mcc_lookup m USING (mcc)
    WHERE NOT t.declined
    GROUP BY m.category
    ORDER BY SUM(t.amount) DESC
    LIMIT 1
),
merchant_volume AS (
    SELECT
        t.merchant_name,
        m.category,
        SUM(t.amount)              AS approved_volume,
        COUNT(*)                   AS tx_count,
        COUNT(DISTINCT t.card_id)  AS unique_cards
    FROM analytics.transactions t
    JOIN analytics.mcc_lookup m USING (mcc)
    JOIN top_cat tc ON tc.category = m.category
    WHERE NOT t.declined
    GROUP BY 1, 2
)
SELECT
    category,
    merchant_name,
    ROUND(approved_volume, 2) AS approved_volume_usd,
    tx_count,
    unique_cards,
    RANK() OVER (ORDER BY approved_volume DESC) AS merchant_rank
FROM merchant_volume
QUALIFY merchant_rank <= 10
ORDER BY merchant_rank;
