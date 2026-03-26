{{ config(materialized='table') }}

with source as (
    select *
    from {{ source('raw_clean', 'fx_rates') }}
),

final as (
    select
        datetime(safe_cast(`timestamp` as timestamp)) as datetime_fetched_UTC,
        upper(base_currency) as base_currency,
        upper(currency) as transaction_currency,
        safe_cast(rate as numeric) as rate
    from source
)

select *
from final
