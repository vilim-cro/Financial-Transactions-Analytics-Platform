{{ config(
    materialized='view',
    schema='feature_store',
    alias='fraud_features_v1_serving'
) }}

select
    * except (is_fraud)
from {{ ref('fraud_features') }}

