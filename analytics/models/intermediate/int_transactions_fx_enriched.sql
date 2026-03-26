{{ config(materialized='table') }}

with tx as (
    select *
    from {{ ref('stg_transactions') }}
),

fx as (
    select *
    from {{ ref('stg_fx_rates') }}
),

tx_fx as (
    select
        tx.*,
        fx.rate as fx_rate_to_currency,
        fx.datetime_fetched_UTC as fx_rate_timestamp_UTC
    from tx
    left join fx
        on tx.currency = fx.transaction_currency
    qualify row_number() over (
        partition by tx.transaction_id
        order by abs(timestamp_diff(
            timestamp(tx.transaction_datetime_UTC),
            timestamp(fx.datetime_fetched_UTC),
            second
        )) asc,
        fx.datetime_fetched_UTC desc
    ) = 1
),

final as (
    select
        *,
        case
            when currency = 'USD' then original_amount
            when fx_rate_to_currency is null or fx_rate_to_currency = 0 then null
            else original_amount / fx_rate_to_currency
        end as amount_usd
    from tx_fx
)

select *
from final
