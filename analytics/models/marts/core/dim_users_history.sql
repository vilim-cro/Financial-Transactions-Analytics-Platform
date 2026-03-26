{{ config(materialized='table') }}

with changes as (
    select *
    from {{ ref('stg_users_changes') }}
),

prepared as (
    select
        user_id,
        first_name,
        last_name,
        gender,
        address,
        city_name,
        zip_code,
        latitude,
        longitude,
        date_of_birth,
        job,
        updated_at,
        raw_loaded_at,
        coalesce(updated_at, raw_loaded_at) as valid_from
    from changes
    where user_id is not null
        and coalesce(updated_at, raw_loaded_at) is not null
),

versioned as (
    select
        *,
        lead(valid_from) over (
            partition by user_id
            order by valid_from, raw_loaded_at
        ) as valid_to
    from prepared
),

final as (
    select
        to_hex(md5(concat(cast(user_id as string), '|', cast(valid_from as string)))) as user_version_id,
        user_id,
        first_name,
        last_name,
        gender,
        address,
        city_name,
        zip_code,
        latitude,
        longitude,
        date_of_birth,
        job,
        updated_at,
        raw_loaded_at,
        valid_from as dbt_valid_from,
        valid_to as dbt_valid_to
    from versioned
)

select *
from final
