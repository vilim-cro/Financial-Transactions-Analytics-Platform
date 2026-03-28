FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir "dbt-bigquery~=1.11.0"

COPY dbt_project.yml ./
COPY models ./models
COPY macros ./macros
COPY analyses ./analyses
COPY seeds ./seeds
COPY tests ./tests

COPY profiles/profiles.yml ./profiles/profiles.yml

ENV DBT_PROFILES_DIR=/app/profiles \
    GOOGLE_APPLICATION_CREDENTIALS=/secrets/dbt-bq-key

ENTRYPOINT ["dbt"]

# 5. Default command
CMD ["build"]
