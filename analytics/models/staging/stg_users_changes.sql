{{ config(materialized='table') }}

with source as (
    select *
    from {{ source('raw_clean', 'users') }}
),

final as (
    select
        _airbyte_emitted_at as raw_loaded_at,
        safe.parse_timestamp(
            '%Y-%m-%dT%H:%M:%E*S%Ez',
            cast(_ab_cdc_updated_at as string)
        ) as updated_at,

        safe_cast(user_id as string) as user_id,
        first_name,
        last_name,

        case
            when upper(gender) = 'M' then 'Male'
            when upper(gender) = 'F' then 'Female'
            else null
        end as gender,

        street as address,
        city as city_name,
        nullif(safe_cast(zip as int64), 0) as zip_code,
        safe_cast(lat as float64) as latitude,
        safe_cast(long as float64) as longitude,

        coalesce(
            safe_cast(json_value(to_json_string(dob), '$.member0') as date),
            safe_cast(json_value(to_json_string(dob), '$.member1') as date)
        ) as date_of_birth,

        job
    from source
)

select *
from final
