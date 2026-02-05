# Sources

This directory contains **source systems and data producers** for the Financial Transactions Analytics Platform: the primary database (PostgreSQL) and the service that streams transaction events into Kafka.

## Contents

| Path | Description |
|------|-------------|
| **postgres/** | PostgreSQL database: Dockerfile, init SQL (schema, data load, CDC setup). Holds `users` and `merchants`; configured for logical replication and publication for CDC (e.g. Airbyte). |
| **transactions/** | **Transactions producer**: reads event CSV, enriches with currency, publishes JSON to Kafka topic `transactions` with checkpointing for resume. |

## Data flow

- **Postgres**: Populated at first run from CSVs (users, merchants) produced by `scripts/prepare_data.py`. Batch job `ingestion/batch/update_users` periodically updates a subset of users to simulate changing dimensions; CDC can stream these changes.
- **Transactions producer**: Reads `credit_card_transactions_events.csv` (created by `scripts/prepare_data.py`), replays events with optional delay, sends each to Kafka. Consumed by `ingestion/streaming` (transactions consumer), which logs and optionally writes batched Parquet to GCS.

See the root [README](../../README.md) for the full architecture.
