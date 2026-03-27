{{ config(materialized='table') }}

with tx as (
    select *
    from {{ ref('fct_transactions') }}
),

final as (
    select
        date_key,
        merchant_name,
        to_hex(md5(concat(cast(date_key as string), '|', cast(merchant_name as string)))) as date_merchant_key,
        count(*) as txn_count,
        countif(is_fraud) as fraud_txn_count,
        safe_divide(countif(is_fraud), count(*)) as fraud_rate,
        sum(coalesce(amount_usd, 0)) as amount_usd_total,
        avg(amount_usd) as amount_usd_avg,
        sum(case when is_fraud then coalesce(amount_usd, 0) else 0 end) as amount_usd_fraud_total,
        count(distinct user_id) as distinct_users
    from tx
    group by date_key, merchant_name
)

select *
from final
