{{ config(materialized='table') }}

with bounds as (
    select
        min(date(transaction_datetime_UTC)) as min_date,
        max(date(transaction_datetime_UTC)) as max_date
    from {{ ref('stg_transactions') }}
),

dates as (
    select
        day_date
    from bounds,
    unnest(generate_date_array(min_date, max_date)) as day_date
),

final as (
    select
        row_number() over (order by day_date) as date_key,
        day_date as date_day,
        extract(year from day_date) as year_number,
        extract(quarter from day_date) as quarter_number,
        extract(month from day_date) as month_number,
        format_date('%B', day_date) as month_name,
        extract(isoweek from day_date) as iso_week_number,
        extract(day from day_date) as day_of_month,
        extract(dayofweek from day_date) as day_of_week,
        format_date('%A', day_date) as day_name,
        extract(isoyear from day_date) as iso_year_number
    from dates
)

select *
from final
