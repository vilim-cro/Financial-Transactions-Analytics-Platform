{% macro train_fraud_lr_v1(project='crypto-minutia-490711-g8', dataset='analytics_ml', model_name='fraud_lr_v1') %}
  {%- set model_fqn -%}`{{ project }}.{{ dataset }}.{{ model_name }}`{%- endset -%}

  {% set sql %}
    create or replace model {{ model_fqn }}
    options(
      model_type = 'logistic_reg',
      input_label_cols = ['is_fraud']
    ) as
    select
      original_amount,
      amount_log1p_original,
      year_number,
      quarter_number,
      month_number,
      iso_week_number,
      day_of_week,
      hour_24,
      cast(is_business_hours as int64) as is_business_hours,
      cast(is_weekend as int64) as is_weekend,
      cast(has_merchant_geo as int64) as has_merchant_geo,
      user_recency_seconds,
      merchant_recency_seconds,
      user_merchant_recency_seconds,
      user_txn_count_24h,
      user_txn_count_30d,
      user_original_amount_sum_24h,
      user_original_amount_avg_24h,
      user_original_amount_max_24h,
      user_original_amount_sum_30d,
      user_original_amount_avg_30d,
      user_original_amount_max_30d,
      merchant_txn_count_30d,
      merchant_original_amount_avg_30d,
      user_merchant_txn_count_30d,
      user_merchant_original_amount_avg_30d,
      is_fraud
    from {{ ref('fraud_features') }}
  {% endset %}

  {% do run_query(sql) %}
  {{ return('trained ' ~ model_fqn) }}
{% endmacro %}

