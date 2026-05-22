-- =============================================================================
-- Theme D — Risk & Operations
-- =============================================================================
-- The "what's going wrong" section of a QBR: declines, fraud signals,
-- geographic concentration risk.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q4.1 — Decline rate by category and over time
-- Business question:
--   Which categories see the highest decline rates, and is the overall
--   decline trend improving or worsening? A spike often means an upstream
--   issue (auth-rule change, BIN range outage) rather than a fraud trend.
-- -----------------------------------------------------------------------------
WITH monthly_cat AS (
    SELECT
        DATE_TRUNC(t.tx_date, MONTH) AS month,
        m.category,
        COUNT(*)                                              AS attempts,
        SUM(CASE WHEN t.declined THEN 1 ELSE 0 END)           AS declines
    FROM analytics.transactions t
    JOIN analytics.mcc_lookup m USING (mcc)
    GROUP BY 1, 2
)
SELECT
    month,
    category,
    attempts,
    declines,
    ROUND(100.0 * declines / NULLIF(attempts, 0), 2) AS decline_rate_pct,
    ROUND(
        100.0 * SUM(declines) OVER (PARTITION BY category ORDER BY month
                                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
              / NULLIF(SUM(attempts) OVER (PARTITION BY category ORDER BY month
                                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0),
        2
    )                                                AS decline_rate_3mo_pct
FROM monthly_cat
ORDER BY month, decline_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- Q4.2 — Fraud indicators
-- Business question:
--   What does the fraud footprint look like — by category, by ticket size,
--   by channel (chip vs swipe)? Used to size fraud-loss provisioning and to
--   prioritize fraud-rule tuning.
-- -----------------------------------------------------------------------------
WITH fraud_stats AS (
    SELECT
        m.category,
        t.use_chip,
        COUNT(*)                                            AS tx_count,
        SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END)         AS fraud_count,
        SUM(CASE WHEN t.is_fraud THEN t.amount END)         AS fraud_volume,
        SUM(t.amount)                                       AS total_volume,
        AVG(CASE WHEN t.is_fraud THEN t.amount END)         AS avg_fraud_ticket
    FROM analytics.transactions t
    JOIN analytics.mcc_lookup m USING (mcc)
    GROUP BY 1, 2
)
SELECT
    category,
    use_chip,
    tx_count,
    fraud_count,
    ROUND(100.0 * fraud_count / NULLIF(tx_count, 0), 3)     AS fraud_rate_pct,
    ROUND(COALESCE(fraud_volume, 0), 2)                     AS fraud_volume_usd,
    ROUND(100.0 * COALESCE(fraud_volume, 0) / NULLIF(total_volume, 0), 3)
                                                            AS fraud_volume_pct,
    ROUND(COALESCE(avg_fraud_ticket, 0), 2)                 AS avg_fraud_ticket_usd
FROM fraud_stats
WHERE fraud_count > 0
ORDER BY fraud_volume_usd DESC;


-- -----------------------------------------------------------------------------
-- Q4.3 — Geographic concentration
-- Business question:
--   Which states drive the most volume, and how concentrated is the
--   portfolio geographically? A top-5-state share above ~50% is a
--   concentration risk worth flagging.
-- -----------------------------------------------------------------------------
WITH state_volume AS (
    SELECT
        merchant_state                          AS state,
        SUM(amount)                             AS approved_volume,
        COUNT(*)                                AS tx_count,
        COUNT(DISTINCT user_id)                 AS unique_users
    FROM analytics.transactions
    WHERE NOT declined
      AND merchant_state IS NOT NULL
    GROUP BY 1
),
ranked AS (
    SELECT
        state,
        approved_volume,
        tx_count,
        unique_users,
        SUM(approved_volume) OVER ()                                AS portfolio_volume,
        SUM(approved_volume) OVER (ORDER BY approved_volume DESC
                                   ROWS BETWEEN UNBOUNDED PRECEDING
                                        AND CURRENT ROW)            AS cumulative_volume,
        RANK() OVER (ORDER BY approved_volume DESC)                 AS state_rank
    FROM state_volume
)
SELECT
    state_rank,
    state,
    ROUND(approved_volume, 2)                                       AS approved_volume_usd,
    tx_count,
    unique_users,
    ROUND(100.0 * approved_volume / portfolio_volume, 2)            AS pct_of_portfolio,
    ROUND(100.0 * cumulative_volume / portfolio_volume, 2)          AS cumulative_pct
FROM ranked
WHERE state_rank <= 15
ORDER BY state_rank;
