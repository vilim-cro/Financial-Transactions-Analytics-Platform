# Batch Ingestion

Scheduled batch jobs for the Financial Transactions Analytics Platform: **FX rates** ingestion to GCS and **user dimension** updates in PostgreSQL. Both run inside a single **batch-cron** container on configurable cron schedules.

## Contents

| Directory / file | Description |
|------------------|-------------|
| **ingest_fx/** | Fetches FX rates from FreeCurrencyAPI and uploads Parquet to GCS under `fx_rates/YYYY/MM/DD/`. |
| **update_users/** | Randomly updates a subset of rows in the Postgres `users` table (city, job, zip) to simulate changing dimensions. |
| **cron/** | Dockerfile and `start-cron.sh` that build one image containing Python, ingest_fx, update_users, and cron. At startup, generates wrapper scripts and crontab; runs both jobs on schedule and optionally runs them once for a quick test. |

## How it runs (batch-cron)

The root `docker-compose.yml` defines a service **batch-cron** that:

1. Builds from `ingestion/batch` using `cron/Dockerfile`.
2. Installs ingest_fx and update_users dependencies and copies their source into the image.
3. On container start, `start-cron.sh` (bash):
   - Resolves GCS credentials path and writes `/app/run-ingest-fx.sh` and `/app/run-update-users.sh` that set env vars and call `uv run python src/...`.
   - Installs a crontab that runs those scripts on the configured schedules (`INGEST_FX_SCHEDULE`, `UPDATE_USERS_SCHEDULE`).
   - Optionally runs each script once for a smoke test.
   - Starts `cron -f` so the container stays up.

No separate containers are built or run for ingest_fx or update_users; they execute in-process inside batch-cron.

## Environment (batch-cron)

Set in compose or `.env`: `POSTGRES_*`, `FREECURRENCYAPI_API_KEY`, `GCS_BUCKET_NAME`, `GOOGLE_APPLICATION_CREDENTIALS`, `INGEST_FX_SCHEDULE`, `UPDATE_USERS_SCHEDULE`. Mount `./credentials` so the GCS key is available at `/app/credentials/`.

## Logs

Inside the container: `/var/log/ingest-fx.log` and `/var/log/update-users.log`. View with:

```bash
docker exec batch-cron cat /var/log/ingest-fx.log
docker exec batch-cron cat /var/log/update-users.log
```
