# Financial Transactions Analytics Platform

A **data engineering and analytics** project that demonstrates end-to-end pipelines for financial transaction data: **streaming ingestion** (Kafka), **batch ingestion** (scheduled jobs, cloud storage), **relational data** (PostgreSQL with CDC), and **cloud storage** (GCS) for analytics-ready datasets.

---

## Overview

This platform simulates a production-style data stack:

- **Event streaming**: Transaction events are produced from a CSV and published to Apache Kafka, then consumed and written to cloud storage in batched Parquet files.
- **Batch jobs**: Scheduled tasks fetch FX rates from an external API and upload them to GCS; another job periodically updates user profile data in PostgreSQL to simulate changing dimension data.
- **Source of truth**: PostgreSQL holds users and merchants; it is configured for **Change Data Capture (CDC)** (logical replication, publication) so downstream systems (e.g. Airbyte) can sync changes.
- **Cloud storage**: The same GCS bucket is used for **FX rates** (date-partitioned Parquet under `fx_rates/`) and **transaction events** (date-partitioned Parquet under `transactions/`), ready for analytics tools (BigQuery, Spark, dbt, etc.).

All services run via **Docker Compose** for local development and demonstration.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  SOURCES                                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (users, merchants)     Transactions Producer (CSV → Kafka)          │
│  • CDC / logical replication       • Checkpointed replay from CSV                │
│  • Publication for Airbyte         • Currency enrichment, topic: transactions   │
└──────────────┬──────────────────────────────────────┬──────────────────────────┘
               │                                      │
               │ CDC (optional)                        │ Kafka
               ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  INGESTION                                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Transactions Consumer              Batch-Cron (single container)               │
│  • Consume from Kafka               • ingest_fx:  fetch FX API → GCS (Parquet)  │
│  • Log each event                   • update_users: random user updates (Postgres)│
│  • Buffer & flush to GCS every 10m • Schedules via cron (env-configurable)      │
│    → transactions/YYYY-MM-DD/*.parquet                                            │
└──────────────┬──────────────────────────────────────┬──────────────────────────┘
               │                                      │
               ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STORAGE & ANALYTICS (GCS)                                                        │
│  • fx_rates/YYYY/MM/DD/fx_rates_*.parquet                                         │
│  • transactions/YYYY-MM-DD/*.parquet                                              │
│  → Downstream: BigQuery, dbt, Spark, etc.                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Layout

| Path | Description |
|------|-------------|
| **`sources/`** | Source systems and data producers: PostgreSQL (schema + CDC), transaction event producer (Kafka). |
| **`ingestion/`** | Ingestion pipelines: **streaming** (Kafka consumer → GCS) and **batch** (ingest_fx, update_users, cron runner). |
| **`scripts/`** | One-off data prep: download Kaggle dataset, split into users/merchants/events CSVs for Postgres and producer. |
| **`docker-compose.yml`** | Defines all services (Zookeeper, Kafka, Postgres, producer, consumer, batch-cron). |
| **`resources/`** | Icons/assets for documentation or UI. |

---

## Prerequisites

- **Docker** and **Docker Compose**
- (Optional) **GCS**: A Google Cloud Storage bucket and a service account JSON key for FX upload and transaction upload. Place the key under `./credentials/` (e.g. `credentials/your-key.json`) and set env vars (see below).
- (Optional) **FreeCurrencyAPI**: API key for FX rates (`ingest_fx`). Get one at [freecurrencyapi.com](https://www.freecurrencyapi.com/).

---

## Quick Start

1. **Prepare data** (first time only):
   - Install [Kaggle CLI](https://github.com/Kaggle/kaggle-api) and set `KAGGLE_USERNAME` / `KAGGLE_KEY`.
   - From project root: `python scripts/prepare_data.py` (or run via `uv` in `scripts/`). This downloads the credit-card transactions dataset and writes:
     - `sources/postgres/init/data/` — users and merchants CSVs for Postgres.
     - `sources/transactions/credit_card_transactions_events.csv` — events for the producer.

2. **Environment** (optional but recommended for full functionality):
   - Copy `.env.example` to `.env` (create one if missing) and set:
     - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
     - `GCS_BUCKET_NAME` — your GCS bucket name
     - `GOOGLE_APPLICATION_CREDENTIALS` — path to key file (e.g. `credentials/your-key.json`)
     - `FREECURRENCYAPI_API_KEY` — for ingest_fx
     - `INGEST_FX_SCHEDULE` / `UPDATE_USERS_SCHEDULE` — cron expressions (defaults in compose)

3. **Run the platform**:
   ```bash
   docker compose up -d
   ```
   - **Postgres** starts with schema and data; CDC init scripts run if present.
   - **Kafka** (+ Zookeeper) and the **transactions producer** start; producer streams events from the CSV to the `transactions` topic.
   - **Transactions consumer** consumes from Kafka, logs events, and (if `GCS_BUCKET_NAME` and credentials are set) buffers and flushes to GCS every 10 minutes as Parquet under `transactions/`.
   - **batch-cron** runs `ingest_fx` and `update_users` on a schedule (e.g. FX every 5 min, user updates every 5 min by default).

4. **Verify**:
   - Producer: `docker logs transactions_producer`
   - Consumer: `docker logs transactions_consumer`
   - Batch jobs: `docker exec batch-cron cat /var/log/ingest-fx.log` and `.../update-users.log`
   - GCS: list objects under `gs://<your-bucket>/fx_rates/` and `gs://<your-bucket>/transactions/`

---

## Services (Docker Compose)

| Service | Role |
|--------|------|
| **zookeeper** | Kafka coordination. |
| **kafka** | Event bus; topic `transactions` used by producer and consumer. |
| **postgres** | Primary database: `users`, `merchants`; logical replication enabled for CDC. |
| **transactions_producer** | Reads events CSV, enriches with currency, produces to Kafka; uses a checkpoint file to resume. |
| **transactions_consumer** | Consumes from Kafka, logs events, buffers and flushes to GCS (Parquet) every 10 minutes. |
| **batch-cron** | Single container that runs **ingest_fx** (FX API → GCS) and **update_users** (random user field updates in Postgres) on cron schedules. |

---

## Data Flows

### 1. Transaction events (streaming)

- **Producer**: Loads `credit_card_transactions_events.csv`, adds `original_amt` and `currency` (from a small FX map), sends JSON to Kafka topic `transactions`. Checkpoints progress so it can resume after restarts.
- **Consumer**: Subscribes to `transactions`, logs each message. If `GCS_BUCKET_NAME` and credentials are set, appends events to an in-memory buffer and **flushes to GCS every 10 minutes** (configurable via `GCS_FLUSH_SECONDS`) as Parquet under `transactions/YYYY-MM-DD/`. Also flushes on shutdown.

### 2. FX rates (batch)

- **ingest_fx** (run by batch-cron): Calls FreeCurrencyAPI, builds a small DataFrame (timestamp, base_currency, currency, rate), writes one Parquet file per run under `fx_rates/YYYY/MM/DD/fx_rates_YYYYMMDD_HHMMSS.parquet`.

### 3. User updates (batch)

- **update_users** (run by batch-cron): Connects to Postgres, selects a random subset of users (configurable percentage), updates one of `city`, `job`, or `zip` with random values. Used to simulate changing dimension data and to drive CDC if you sync Postgres to a warehouse.

### 4. PostgreSQL and CDC

- **Schema**: `users` (e.g. user_id, name, city, job, zip, dob), `merchants` (merchant, coordinates, zip). Init scripts load from CSV.
- **CDC**: Logical replication enabled; replication slot and publication (e.g. `airbyte_publication`) for all tables so tools like Airbyte can consume change streams.

---

## Configuration (environment)

Relevant variables (set in `.env` or `docker-compose`):

| Variable | Used by | Purpose |
|----------|--------|---------|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | postgres, batch-cron, update_users | Database connection. |
| `KAFKA_BROKER` | producer, consumer | Kafka bootstrap (default `kafka:9092`). |
| `GCS_BUCKET_NAME` | transactions_consumer, batch-cron (ingest_fx) | Target GCS bucket. |
| `GOOGLE_APPLICATION_CREDENTIALS` | consumer, batch-cron | Path to GCP service account JSON (e.g. `credentials/key.json`). |
| `GCS_FLUSH_SECONDS` | transactions_consumer | Seconds between GCS flushes (default 600 = 10 min). |
| `FREECURRENCYAPI_API_KEY` | batch-cron (ingest_fx) | FX API key. |
| `INGEST_FX_SCHEDULE`, `UPDATE_USERS_SCHEDULE` | batch-cron | Cron expressions for ingest_fx and update_users. |

Mount `./credentials` into containers that need GCS (consumer and batch-cron) so the path in `GOOGLE_APPLICATION_CREDENTIALS` resolves inside the container.

---

## Tech Stack

- **Streaming**: Apache Kafka (Confluent), Python (`kafka-python`), checkpointed producer, consumer with time-based batching.
- **Batch / scheduling**: Cron in a single container; Python jobs for FX and user updates; same GCS bucket, different prefixes.
- **Storage**: PostgreSQL (schema design, CSV load, logical replication / CDC); Google Cloud Storage (Parquet).
- **Data formats**: JSON (Kafka), Parquet (GCS), CSV (sources and prep).
- **Infrastructure**: Docker, Docker Compose; env-based config; bind-mounted credentials.
- **Languages / tools**: Python 3.11, pandas, pyarrow, `google-cloud-storage`, `psycopg2`, `uv` for dependency management.

---

## License

See [LICENSE](LICENSE).
