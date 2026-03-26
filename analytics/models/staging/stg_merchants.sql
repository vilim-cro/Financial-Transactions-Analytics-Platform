{{ config(materialized='table') }}

with source as (
    select *
    from {{ source('raw_clean', 'merchants') }}
),

final as (
    select
        _airbyte_emitted_at as raw_loaded_at,
        regexp_replace(merchant, r'^fraud_', '') as merchant_name,
        safe_cast(merch_lat as float64) as merchant_latitude,
        safe_cast(merch_long as float64) as merchant_longitude,
        nullif(safe_cast(merch_zipcode as int64), 0) as merchant_zipcode
    from source
)

select *
from final
