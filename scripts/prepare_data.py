import pandas as pd
import uuid
import os
import kagglehub
from pathlib import Path

def make_user_id(first_name, last_name):
    key = f"{first_name.lower()}|{last_name.lower()}"
    return uuid.uuid5(uuid.NAMESPACE_DNS, key)


# Get the project root directory (parent of scripts/)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

path = kagglehub.dataset_download("priyamchoksi/credit-card-transactions-dataset")

df = pd.read_csv(os.path.join(path, "credit_card_transactions.csv"))
user_keys = (
    df["first"].str.lower().str.strip()
    + "|"
    + df["last"].str.lower().str.strip()
)
df["user_id"] = user_keys.map(
    lambda k: uuid.uuid5(uuid.NAMESPACE_DNS, k)
)
df.rename(columns={"first": "first_name", "last": "last_name"}, inplace=True)
df["merch_zipcode"] = df["merch_zipcode"].fillna(0).astype(int)

DATA_PATH_EVENTS = PROJECT_ROOT / "sources/transactions/credit_card_transactions_events.csv"
DATA_PATH_USERS = PROJECT_ROOT / "sources/postgres/init/data/credit_card_transactions_users.csv"
DATA_PATH_MERCHANTS = PROJECT_ROOT / "sources/postgres/init/data/credit_card_transactions_merchants.csv"
DATA_PATH_EVENTS.parent.mkdir(parents=True, exist_ok=True)
DATA_PATH_USERS.parent.mkdir(parents=True, exist_ok=True)

df_events = df[["trans_date_trans_time", "user_id", "merchant", "category", "amt", "trans_num", "unix_time", "is_fraud"]]
df_events.to_csv(DATA_PATH_EVENTS, index=False, sep=";")

df_users = df[["user_id", "first_name", "last_name", "gender", "street", "city", "zip", "lat", "long", "job", "dob"]].drop_duplicates(subset=["user_id"])
df_users.to_csv(DATA_PATH_USERS, index=False, sep=";")

df_merch = df[["merchant", "merch_lat", "merch_long", "merch_zipcode"]].drop_duplicates(subset=["merchant"])
df_merch.to_csv(DATA_PATH_MERCHANTS, index=False, sep=";")
