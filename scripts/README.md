# Scripts

One-off and utility scripts for the Financial Transactions Analytics Platform.

## prepare_data.py

**Purpose**: Download the [Credit Card Transactions dataset](https://www.kaggle.com/datasets/priyamchoksi/credit-card-transactions-dataset) from Kaggle and split it into the files required by the rest of the project.

**What it does**:

1. Uses **kagglehub** to download the dataset (requires Kaggle API credentials: `KAGGLE_USERNAME` and `KAGGLE_KEY` in the environment or `~/.kaggle/kaggle.json`).
2. Reads `credit_card_transactions.csv`, derives deterministic **user_id**s from first/last name (UUID v5).
3. Writes three outputs:
   - **Events**: `sources/transactions/credit_card_transactions_events.csv` — columns used by the transaction producer (e.g. trans_date_trans_time, user_id, merchant, category, amt, is_fraud, etc.).
   - **Users**: `sources/postgres/init/data/credit_card_transactions_users.csv` — one row per user for the `users` table (user_id, first_name, last_name, gender, street, city, zip, lat, long, job, dob).
   - **Merchants**: `sources/postgres/init/data/credit_card_transactions_merchants.csv` — one row per merchant for the `merchants` table.

**When to run**: Once before first bringing up Postgres and the transactions producer, so that init scripts and the producer have the correct CSV paths.

**Run** (from project root or scripts dir):

```bash
cd scripts
uv sync
export KAGGLE_USERNAME=... KAGGLE_KEY=...
uv run python prepare_data.py
```

Or from project root:

```bash
python scripts/prepare_data.py
```

(Ensure `scripts/` dependencies are installed and Kaggle is configured.)
