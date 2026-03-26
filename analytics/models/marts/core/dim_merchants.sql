{{ config(materialized='table') }}

with final as (
    select
        merchant_name,
        merchant_latitude,
        merchant_longitude,
        merchant_zipcode,
        raw_loaded_at
    from {{ ref('stg_merchants') }}
)

select *
from final
