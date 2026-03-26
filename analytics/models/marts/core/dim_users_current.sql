{{ config(materialized='table') }}

select
    user_version_id,
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
    dbt_valid_from
from {{ ref('dim_users_history') }}
where dbt_valid_to is null
