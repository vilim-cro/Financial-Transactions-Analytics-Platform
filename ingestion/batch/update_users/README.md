# Update Users (Batch Job)

Batch script that **randomly updates a subset of user records** in the PostgreSQL `users` table (e.g. `city`, `job`, `zip`) to simulate changing dimension data. Used to demonstrate batch updates and to generate ongoing changes for CDC if the database is synced to a data warehouse (e.g. via Airbyte).

## Role in the platform

- **Input**: PostgreSQL database (`users` table) — connection via `POSTGRES_*` env vars.
- **Behavior**: Selects a random sample of users (percentage configurable via `UPDATE_PERCENTAGE`), picks one of the updatable fields (`city`, `job`, `zip`), and sets it to a random value from predefined lists (cities, job titles, or zip range).
- **Output**: Only the `users` table is modified; **merchants** are not updated.

This job is intended to be run on a **schedule** (e.g. by the shared `batch-cron` container in this repo), so that dimension data changes over time and CDC pipelines can stream those changes.

## Configuration

| Env var | Default | Description |
|--------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | Database host (use `postgres` in Docker). |
| `POSTGRES_PORT` | `5433` | Database port (use `5432` inside Docker). |
| `POSTGRES_DB` | `all_users` | Database name. |
| `POSTGRES_USER` | `postgres` | Database user. |
| `POSTGRES_PASSWORD` | `postgres` | Database password. |
| `UPDATE_PERCENTAGE` | `0.01` | Fraction of users to update per run (e.g. 0.01 = 1%). |

Updatable fields and value pools (cities, jobs) are defined in `src/config.py`.

## Run locally

From this directory:

```bash
uv sync
export POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_DB=all_users POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres
uv run python src/update_user_data.py
```

## Docker / batch-cron

This script is not run as a standalone container. It is executed **in-process** by the `batch-cron` service (see `ingestion/batch/cron/`), which runs both `ingest_fx` and `update_users` on cron schedules. Set `UPDATE_USERS_SCHEDULE` (cron expression) and `POSTGRES_*` in the batch-cron environment.
