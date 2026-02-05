# Transactions Consumer (Streaming Ingestion)

Kafka consumer that reads **credit card transaction events** from the `transactions` topic, logs them, and (when configured) **writes batched Parquet files to Google Cloud Storage** under the `transactions/` prefix for analytics.

## Role in the platform

- **Input**: JSON messages from Kafka topic `transactions` (produced by `sources/transactions`).
- **Behavior**: Consumes messages in a loop, logs each event (timestamp, user, merchant, category, amount, fraud flag), and optionally buffers events in memory.
- **Output**: If `GCS_BUCKET_NAME` and valid GCP credentials are set, the consumer flushes the buffer to GCS every **10 minutes** (configurable via `GCS_FLUSH_SECONDS`) and on shutdown. Files are written as **Parquet** under `transactions/YYYY-MM-DD/YYYY-MM-DDTHH-mm-ss_<batch_index>.parquet` in the same bucket used by other services (e.g. FX rates).

If GCS is not configured, the service runs in **log-only** mode (no uploads), which is useful for local development without cloud credentials.

## Design choices

- **Time-based batching**: Flush every N seconds (default 600) and on shutdown to limit the number of GCS writes and to produce fewer, larger files for downstream analytics.
- **Parquet**: Same format as the FX pipeline; columnar and compact, suitable for BigQuery/Spark/dbt.
- **Credentials**: Uses the same pattern as `ingest_fx`: `GOOGLE_APPLICATION_CREDENTIALS` with resolution for relative paths and `/app/credentials` when run in Docker.

## Configuration

| Env var | Default | Description |
|--------|---------|-------------|
| `KAFKA_BROKER` | `kafka:9092` | Kafka bootstrap servers. |
| `KAFKA_TOPIC` | `transactions` | Topic to consume. |
| `KAFKA_CONSUMER_GROUP` | `transactions-consumer-group` | Consumer group ID. |
| `GCS_BUCKET_NAME` | (empty) | If set, enable GCS upload; otherwise log-only. |
| `GOOGLE_APPLICATION_CREDENTIALS` | (see config) | Path to GCP service account JSON. |
| `GCS_FLUSH_SECONDS` | `600` | Seconds between buffer flushes to GCS. |

## Run locally

From this directory (with `uv` and Kafka reachable):

```bash
uv sync
export KAFKA_BROKER=localhost:9092
# Optional: GCS_BUCKET_NAME, GOOGLE_APPLICATION_CREDENTIALS for uploads
uv run python src/event_consumer.py
```

## Docker

Built and run via root `docker-compose` as the `transactions_consumer` service. Mount `./credentials` so the container can read the GCP key; set `GCS_BUCKET_NAME` and `GOOGLE_APPLICATION_CREDENTIALS` in the compose environment.
