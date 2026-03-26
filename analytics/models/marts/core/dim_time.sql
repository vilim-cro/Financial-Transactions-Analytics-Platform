{{ config(materialized='table') }}

with seconds as (
    select
        sec
    from unnest(generate_array(0, 86399)) as sec
),

base as (
    select
        time_add(time(0, 0, 0), interval sec second) as time_of_day
    from seconds
),

final as (
    select
        cast(format_time('%H%M%S', time_of_day) as int64) as time_key,
        time_of_day,
        extract(hour from time_of_day) as hour_24,
        extract(minute from time_of_day) as minute_number,
        extract(second from time_of_day) as second_number,
        format_time('%H:00-%H:59', time_of_day) as hour_bucket,
        case
            when extract(hour from time_of_day) between 0 and 5 then 'Night'
            when extract(hour from time_of_day) between 6 and 11 then 'Morning'
            when extract(hour from time_of_day) between 12 and 17 then 'Afternoon'
            else 'Evening'
        end as part_of_day,
        case
            when extract(hour from time_of_day) between 9 and 16 then true
            else false
        end as is_business_hours
    from base
)

select *
from final
