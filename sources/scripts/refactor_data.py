import pandas as pd
import uuid

def make_user_id(first_name, last_name):
    key = f"{first_name.lower()}|{last_name.lower()}"
    return uuid.uuid5(uuid.NAMESPACE_DNS, key)

df = pd.read_csv("../../resources/kaggle_datasets/credit_card_transactions.csv")
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

df_events = df[["trans_date_trans_time", "user_id", "merchant", "category", "amt", "trans_num", "unix_time", "is_fraud"]]
df_events.to_csv("../../docker/postgres/init/data/credit_card_transactions_events.csv", index=False, sep=";")

df_users = df[["user_id", "first_name", "last_name", "gender", "street", "city", "zip", "lat", "long", "job", "dob"]].drop_duplicates(subset=["user_id"])
df_users.to_csv("../../docker/postgres/init/data/credit_card_transactions_users.csv", index=False, sep=";")

df_merch = df[["merchant", "merch_lat", "merch_long", "merch_zipcode"]].drop_duplicates(subset=["merchant"])
df_merch.to_csv("../../docker/postgres/init/data/credit_card_transactions_merchants.csv", index=False, sep=";")
