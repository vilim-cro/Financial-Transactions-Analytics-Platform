{{ config(
    materialized='table',
    schema='analytics_ml',
    alias='fraud_predictions_v1',
    tags=['ml', 'predictions']
) }}

-- Run after feature store: dbt run --select fraud_features fraud_features_serving fraud_predictions

with scored as (
    select *
    from ml.predict(
        model `{{ var('bqml_model_fqn') }}`,
        (
            select
                * except (is_business_hours, is_weekend, has_merchant_geo),
                -- Match train_fraud_lr_v1.sql: BOOL -> INT64 (BQML rejects BOOL at predict time)
                cast(is_business_hours as int64) as is_business_hours,
                cast(is_weekend as int64) as is_weekend,
                cast(has_merchant_geo as int64) as has_merchant_geo
            from {{ ref('fraud_features_serving') }}
        )
    )
),

with_prob as (
    select
        transaction_id,
        (
            select prob
            from unnest(predicted_is_fraud_probs) as probs
            where probs.label is true
            limit 1
        ) as fraud_probability
    from scored
)

select
    transaction_id,
    fraud_probability,
    fraud_probability >= {{ var('fraud_probability_threshold') }} as predicted_fraud,
    current_timestamp() as predicted_at
from with_prob
