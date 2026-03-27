{{ config(materialized='table') }}

with tx as (
    select *
    from {{ ref('fct_transactions') }}
),

dim_time as (
    select
        time_key,
        hour_24
    from {{ ref('dim_time') }}
),

enriched as (
    select
        tx.*,
        dim_time.hour_24
    from tx
    left join dim_time
        on tx.time_key = dim_time.time_key
),

final as (
    select
        date_key,
        time_key,
        count(*) as txn_count,
        countif(is_fraud) as fraud_txn_count,
        safe_divide(countif(is_fraud), count(*)) as fraud_rate,
        sum(coalesce(amount_usd, 0)) as amount_usd_total,
        avg(amount_usd) as amount_usd_avg,
        sum(case when is_fraud then coalesce(amount_usd, 0) else 0 end) as amount_usd_fraud_total,
        count(distinct user_id) as distinct_users,
        count(distinct merchant_name) as distinct_merchants
    from enriched
    group by date_key, time_key
)

select *
from final
