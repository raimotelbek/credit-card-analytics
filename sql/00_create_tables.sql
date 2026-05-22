-- =============================================================================
-- BigQuery DDL — credit_card_analytics dataset
-- =============================================================================
-- Run once in BigQuery before loading data via python/load_to_bigquery.py.
-- The Python loader uses WRITE_TRUNCATE, so these CREATE statements are only
-- needed if you want to set up partitioning/clustering ahead of time without
-- letting the loader infer schema.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS credit_card_analytics
OPTIONS (location = 'US');


CREATE TABLE IF NOT EXISTS credit_card_analytics.transactions (
    user_id         INT64,
    card_id         INT64,
    tx_date         DATE,
    year            INT64,
    month           INT64,
    day             INT64,
    time            STRING,
    amount          FLOAT64,
    use_chip        STRING,
    merchant_name   STRING,
    merchant_city   STRING,
    merchant_state  STRING,
    zip             STRING,
    mcc             INT64,
    errors          STRING,
    is_fraud        BOOL,
    declined        BOOL
)
PARTITION BY tx_date
CLUSTER BY mcc, merchant_state;


CREATE TABLE IF NOT EXISTS credit_card_analytics.users (
    user_id         INT64,
    signup_date     DATE,
    birth_year      INT64,
    gender          STRING,
    state           STRING,
    yearly_income   INT64,
    credit_score    INT64
);


CREATE TABLE IF NOT EXISTS credit_card_analytics.cards (
    card_id         INT64,
    user_id         INT64,
    card_brand      STRING,
    card_type       STRING,
    issue_date      DATE,
    expires         DATE,
    has_chip        BOOL
);


CREATE TABLE IF NOT EXISTS credit_card_analytics.mcc_lookup (
    mcc             INT64,
    category        STRING
);
