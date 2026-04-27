{{ config(
    materialized='table',
    schema='feature_store',
    alias='fraud_features_v1'
) }}

with base as (
    select
        transaction_id,
        user_id,
        merchant_name,
        transaction_datetime_UTC,
        timestamp(transaction_datetime_UTC) as event_ts,
        unix_time_seconds,
        date_key,
        time_key,
        original_amount,
        is_fraud
    from {{ ref('fct_transactions') }}
),

date_dim as (
    select
        date_key,
        year_number,
        quarter_number,
        month_number,
        iso_week_number,
        day_of_week,
        day_name
    from {{ ref('dim_date') }}
),

time_dim as (
    select
        time_key,
        hour_24,
        part_of_day,
        is_business_hours
    from {{ ref('dim_time') }}
),

merchant_dim as (
    select
        merchant_name,
        merchant_latitude,
        merchant_longitude,
        merchant_zipcode
    from {{ ref('dim_merchants') }}
),

enriched as (
    select
        b.*,
        d.year_number,
        d.quarter_number,
        d.month_number,
        d.iso_week_number,
        d.day_of_week,
        d.day_name,
        t.hour_24,
        t.part_of_day,
        t.is_business_hours,
        (d.day_of_week in (1, 7)) as is_weekend,
        m.merchant_latitude,
        m.merchant_longitude,
        m.merchant_zipcode,
        (m.merchant_latitude is not null and m.merchant_longitude is not null) as has_merchant_geo
    from base b
    left join date_dim d
        on b.date_key = d.date_key
    left join time_dim t
        on b.time_key = t.time_key
    left join merchant_dim m
        on b.merchant_name = m.merchant_name
),

features as (
    select
        -- identifiers
        transaction_id,
        user_id,
        merchant_name,
        transaction_datetime_UTC,
        unix_time_seconds,

        -- label (keep for training; exclude when building a serving SELECT)
        is_fraud,

        -- raw amount features (no currency/FX info allowed)
        original_amount,
        ln(1 + cast(original_amount as float64)) as amount_log1p_original,

        -- calendar/time features
        year_number,
        quarter_number,
        month_number,
        iso_week_number,
        day_of_week,
        day_name,
        hour_24,
        part_of_day,
        is_business_hours,
        is_weekend,

        -- merchant profile features
        merchant_latitude,
        merchant_longitude,
        merchant_zipcode,
        has_merchant_geo,

        -- recency features (point-in-time by construction)
        timestamp_diff(
            event_ts,
            lag(event_ts) over (partition by user_id order by event_ts, transaction_id),
            second
        ) as user_recency_seconds,
        timestamp_diff(
            event_ts,
            lag(event_ts) over (partition by merchant_name order by event_ts, transaction_id),
            second
        ) as merchant_recency_seconds,
        timestamp_diff(
            event_ts,
            lag(event_ts) over (partition by user_id, merchant_name order by event_ts, transaction_id),
            second
        ) as user_merchant_recency_seconds,

        -- rolling-window aggregates (strictly prior events only)
        count(*) over (
            partition by user_id
            order by unix_time_seconds
            range between 86400 preceding and 1 preceding
        ) as user_txn_count_24h,
        count(*) over (
            partition by user_id
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as user_txn_count_30d,

        sum(original_amount) over (
            partition by user_id
            order by unix_time_seconds
            range between 86400 preceding and 1 preceding
        ) as user_original_amount_sum_24h,
        avg(original_amount) over (
            partition by user_id
            order by unix_time_seconds
            range between 86400 preceding and 1 preceding
        ) as user_original_amount_avg_24h,
        max(original_amount) over (
            partition by user_id
            order by unix_time_seconds
            range between 86400 preceding and 1 preceding
        ) as user_original_amount_max_24h,

        sum(original_amount) over (
            partition by user_id
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as user_original_amount_sum_30d,
        avg(original_amount) over (
            partition by user_id
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as user_original_amount_avg_30d,
        max(original_amount) over (
            partition by user_id
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as user_original_amount_max_30d,

        -- merchant aggregates
        count(*) over (
            partition by merchant_name
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as merchant_txn_count_30d,
        avg(original_amount) over (
            partition by merchant_name
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as merchant_original_amount_avg_30d,

        -- user-merchant interaction aggregates
        count(*) over (
            partition by user_id, merchant_name
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as user_merchant_txn_count_30d,
        avg(original_amount) over (
            partition by user_id, merchant_name
            order by unix_time_seconds
            range between 2592000 preceding and 1 preceding
        ) as user_merchant_original_amount_avg_30d

    from enriched
)

select *
from features
