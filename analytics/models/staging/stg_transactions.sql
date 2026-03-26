{{ config(materialized='table') }}

with source as (
    select *
    from {{ source('raw_clean', 'transactions') }}
),

final as (
    select
        safe_cast(user_id as string) as user_id,
        safe_cast(trans_num as string) as transaction_id,
        safe_cast(trans_date_trans_time as datetime) as transaction_datetime_UTC,
        regexp_replace(merchant, r'^fraud_', '') as merchant_name,
        safe_cast(unix_time as int64) as unix_time_seconds,
        safe_cast(original_amt as numeric) as original_amount,
        upper(currency) as currency,
        safe_cast(is_fraud as bool) as is_fraud,

        -- keep any remaining raw columns for forward compatibility
        * except (
            user_id,
            trans_num,
            trans_date_trans_time,
            merchant,
            unix_time,
            original_amt,
            currency,
            is_fraud
        )
    from source
)

select *
from final
