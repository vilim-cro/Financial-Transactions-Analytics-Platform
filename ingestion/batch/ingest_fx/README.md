# Ingest FX (Batch Job)

Fetches **foreign exchange rates** from the [FreeCurrencyAPI](https://www.freecurrencyapi.com/) and uploads them to **Google Cloud Storage** as a single Parquet file per run. Used to build a time-series dataset of FX rates in the same GCS bucket as transaction data, for analytics or joins (e.g. in BigQuery or dbt).

## Role in the platform

- **Input**: FreeCurrencyAPI (requires `FREECURRENCYAPI_API_KEY`). Currencies to fetch are set in `src/config.py` (e.g. EUR, GBP, etc.).
- **Output**: One Parquet file per run under `fx_rates/YYYY/MM/DD/fx_rates_YYYYMMDD_HHMMSS.parquet`. Each row has `timestamp`, `base_currency` (USD), `currency`, and `rate`.
- **Credentials**: Uses `GOOGLE_APPLICATION_CREDENTIALS` (path to GCP service account JSON), with resolution for relative paths and `/app/credentials` when run in Docker.

This job is not run as a standalone container; it is executed **in-process** by the **batch-cron** service (see `ingestion/batch/cron/` and `ingestion/batch/README.md`), which runs it on a cron schedule (e.g. every 5 minutes).

## Configuration

| Env var | Description |
|--------|-------------|
| `FREECURRENCYAPI_API_KEY` | Required. API key from freecurrencyapi.com. |
| `GCS_BUCKET_NAME` | Required. Target GCS bucket name. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON (e.g. `credentials/your-key.json`). |

## Run locally

From this directory:

```bash
uv sync
export FREECURRENCYAPI_API_KEY=... GCS_BUCKET_NAME=... GOOGLE_APPLICATION_CREDENTIALS=...
uv run python src/get_fx_rates.py
```

## Docker / batch-cron

Scheduled by batch-cron; set `INGEST_FX_SCHEDULE` (cron expression) and the env vars above in the batch-cron service. Mount `./credentials` so the key file is available at `/app/credentials/` inside the container.
