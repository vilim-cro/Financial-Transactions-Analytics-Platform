{{ config(materialized='table') }}

with tx as (
    select *
    from {{ ref('fct_transactions') }}
),

dim_date as (
    select
        date_key,
        date_day
    from {{ ref('dim_date') }}
),

dim_users as (
    select
        user_id,
        gender,
        date_of_birth
    from {{ ref('dim_users_current') }}
),

enriched as (
    select
        tx.date_key,
        tx.transaction_id,
        tx.user_id,
        tx.merchant_name,
        tx.amount_usd,
        tx.is_fraud,
        coalesce(dim_users.gender, 'Unknown') as gender,
        case
            when dim_users.date_of_birth is null then 'Unknown'
            when date_diff(dim_date.date_day, dim_users.date_of_birth, year) < 25 then '<25'
            when date_diff(dim_date.date_day, dim_users.date_of_birth, year) between 25 and 34 then '25-34'
            when date_diff(dim_date.date_day, dim_users.date_of_birth, year) between 35 and 44 then '35-44'
            when date_diff(dim_date.date_day, dim_users.date_of_birth, year) between 45 and 54 then '45-54'
            else '55+'
        end as age_band
    from tx
    left join dim_date
        on tx.date_key = dim_date.date_key
    left join dim_users
        on tx.user_id = dim_users.user_id
),

final as (
    select
        date_key,
        gender,
        age_band,
        to_hex(md5(concat(
            cast(date_key as string), '|',
            cast(gender as string), '|',
            cast(age_band as string)
        ))) as date_user_segment_key,
        count(*) as txn_count,
        countif(is_fraud) as fraud_txn_count,
        safe_divide(countif(is_fraud), count(*)) as fraud_rate,
        sum(coalesce(amount_usd, 0)) as amount_usd_total,
        avg(amount_usd) as amount_usd_avg,
        sum(case when is_fraud then coalesce(amount_usd, 0) else 0 end) as amount_usd_fraud_total,
        count(distinct user_id) as distinct_users,
        count(distinct merchant_name) as distinct_merchants
    from enriched
    group by date_key, gender, age_band
)

select *
from final
