-- =============================================================================
-- Theme C — Customer Behavior
-- =============================================================================
-- "Who are our cardholders and how do they actually use the product?"
-- Cohort retention, spender concentration, multi-card usage, engagement.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q3.1 — Customer cohort retention by signup month
-- Business question:
--   Of users who signed up in month M, what % are still transacting N months
--   later? Reveals which acquisition vintages are stickiest. Classic cohort
--   triangle.
-- -----------------------------------------------------------------------------
WITH cohort_size AS (
    -- everyone who signed up in a given month, regardless of whether
    -- they ever transacted (the denominator)
    SELECT
        DATE_TRUNC(signup_date, MONTH) AS cohort_month,
        COUNT(*)                       AS cohort_users
    FROM analytics.users
    GROUP BY 1
),
user_activity AS (
    SELECT DISTINCT
        u.user_id,
        DATE_TRUNC(u.signup_date, MONTH) AS cohort_month,
        DATE_TRUNC(t.tx_date,    MONTH)  AS active_month
    FROM analytics.users u
    JOIN analytics.transactions t USING (user_id)
    WHERE NOT t.declined
      AND t.tx_date >= u.signup_date
),
with_offset AS (
    SELECT
        cohort_month,
        user_id,
        DATE_DIFF(active_month, cohort_month, MONTH) AS months_since_signup
    FROM user_activity
)
SELECT
    w.cohort_month,
    cs.cohort_users,
    w.months_since_signup,
    COUNT(DISTINCT w.user_id) AS retained_users,
    ROUND(100.0 * COUNT(DISTINCT w.user_id) / NULLIF(cs.cohort_users, 0), 2)
                              AS retention_pct
FROM with_offset w
JOIN cohort_size cs USING (cohort_month)
WHERE w.months_since_signup BETWEEN 0 AND 12
GROUP BY 1, 2, 3
ORDER BY w.cohort_month, w.months_since_signup;


-- -----------------------------------------------------------------------------
-- Q3.2 — Spender concentration (Pareto)
-- Business question:
--   How concentrated is spend? Compare the top 10% of spenders vs. the
--   bottom 50%. An 80/20 distribution is normal; 95/5 is a warning sign
--   (heavily dependent on a few whales).
-- -----------------------------------------------------------------------------
WITH user_spend AS (
    SELECT
        user_id,
        SUM(amount) AS total_spend,
        COUNT(*)    AS tx_count
    FROM analytics.transactions
    WHERE NOT declined
    GROUP BY 1
),
deciled AS (
    SELECT
        user_id,
        total_spend,
        tx_count,
        NTILE(10) OVER (ORDER BY total_spend DESC) AS spend_decile
    FROM user_spend
)
SELECT
    CASE
        WHEN spend_decile = 1 THEN 'Top 10%'
        WHEN spend_decile <= 5 THEN 'Middle 40%'
        ELSE 'Bottom 50%'
    END                                            AS spender_tier,
    COUNT(*)                                       AS users,
    ROUND(SUM(total_spend), 2)                     AS total_spend_usd,
    ROUND(AVG(total_spend), 2)                     AS avg_spend_per_user_usd,
    ROUND(100.0 * SUM(total_spend) /
        SUM(SUM(total_spend)) OVER (), 2)          AS pct_of_total_spend
FROM deciled
GROUP BY 1
ORDER BY pct_of_total_spend DESC;


-- -----------------------------------------------------------------------------
-- Q3.3 — Multi-card user analysis
-- Business question:
--   What share of users hold multiple cards, and do multi-card users transact
--   more? Multi-card cohorts are typically higher LTV and better cross-sell
--   targets.
-- -----------------------------------------------------------------------------
WITH user_cards AS (
    SELECT user_id, COUNT(*) AS card_count
    FROM analytics.cards
    GROUP BY 1
),
user_spend AS (
    SELECT
        user_id,
        SUM(amount) AS total_spend,
        COUNT(*)    AS tx_count
    FROM analytics.transactions
    WHERE NOT declined
    GROUP BY 1
)
SELECT
    CASE
        WHEN uc.card_count = 1            THEN '1 card'
        WHEN uc.card_count = 2            THEN '2 cards'
        WHEN uc.card_count BETWEEN 3 AND 4 THEN '3-4 cards'
        ELSE '5+ cards'
    END                                                AS card_cohort,
    COUNT(DISTINCT uc.user_id)                         AS users,
    ROUND(AVG(COALESCE(us.total_spend, 0)), 2)         AS avg_spend_per_user_usd,
    ROUND(AVG(COALESCE(us.tx_count, 0)), 2)            AS avg_tx_per_user,
    ROUND(SUM(COALESCE(us.total_spend, 0)), 2)         AS cohort_volume_usd
FROM user_cards uc
LEFT JOIN user_spend us USING (user_id)
GROUP BY 1
ORDER BY MIN(uc.card_count);


-- -----------------------------------------------------------------------------
-- Q3.4 — Average transactions per active user per month
-- Business question:
--   Engagement frequency — how often does an active user actually swipe?
--   Tracking this alongside active-card-rate separates "we have more
--   users" from "our users use us more often".
-- -----------------------------------------------------------------------------
WITH user_month AS (
    SELECT
        DATE_TRUNC(tx_date, MONTH) AS month,
        user_id,
        COUNT(*)                   AS tx_count
    FROM analytics.transactions
    WHERE NOT declined
    GROUP BY 1, 2
)
SELECT
    month,
    COUNT(DISTINCT user_id)                AS active_users,
    SUM(tx_count)                          AS total_tx,
    ROUND(AVG(tx_count), 2)                AS avg_tx_per_active_user,
    ROUND(APPROX_QUANTILES(tx_count, 100)[OFFSET(50)], 2) AS median_tx_per_active_user
FROM user_month
GROUP BY 1
ORDER BY 1;
