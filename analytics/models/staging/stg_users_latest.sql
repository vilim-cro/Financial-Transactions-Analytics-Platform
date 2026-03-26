{{ config(materialized='table') }}

with changes as (
    select *
    from {{ ref('stg_users_changes') }}
),

latest as (
    select
        *
    from changes
    qualify row_number() over (
        partition by user_id
        order by updated_at desc, raw_loaded_at desc
    ) = 1
)

select *
from latest
