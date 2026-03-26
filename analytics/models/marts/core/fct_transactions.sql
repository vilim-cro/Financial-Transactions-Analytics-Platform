{{ config(materialized='table') }}

with tx as (
    select *
    from {{ ref('int_transactions_fx_enriched') }}
),

users_hist as (
    select *
    from {{ ref('dim_users_history') }}
),

dim_date as (
    select
        date_key,
        date_day
    from {{ ref('dim_date') }}
),

final as (
    select
        tx.transaction_id,
        tx.user_id,
        users_hist.user_version_id,
        tx.merchant_name,
        dim_date.date_key,
        cast(format_datetime('%H%M%S', tx.transaction_datetime_UTC) as int64) as time_key,
        tx.transaction_datetime_UTC,
        tx.unix_time_seconds,
        tx.currency,
        tx.original_amount,
        tx.fx_rate_to_currency,
        tx.fx_rate_timestamp_UTC,
        tx.amount_usd,
        tx.is_fraud
    from tx
    left join users_hist
        on tx.user_id = users_hist.user_id
        and timestamp(tx.transaction_datetime_UTC) >= users_hist.dbt_valid_from
        and timestamp(tx.transaction_datetime_UTC) < coalesce(users_hist.dbt_valid_to, timestamp('9999-12-31'))
    left join dim_date
        on date(tx.transaction_datetime_UTC) = dim_date.date_day
)

select *
from final
