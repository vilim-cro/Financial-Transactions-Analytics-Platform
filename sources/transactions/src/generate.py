import pandas as pd
import time
import random

df = pd.read_csv("credit_card_transactions_events.csv", sep=";")
df.rename(columns={"amt": "usd_amt"}, inplace=True)

# Load checkpoint to see where it left off
with open("checkpoint.txt", "r") as f:
    last_idx = int(f.read())

rates_to_usd = {
    "EUR": 1.17,
    "DKK": 0.16,
    "SEK": 0.11,
    "NOK": 0.10
}

for idx in range(last_idx, len(df) - 1):
    event = df.iloc[idx]

    # Simulate payments in different currrencies
    currency = random.choice(list(rates_to_usd.keys()))
    original_amt = event["usd_amt"] / rates_to_usd[currency]
    event["original_amt"] = original_amt
    event["currency"] = currency
    event = event.drop(columns=["usd_amount"])

    # Produce event
    print(event)

    # Save checkpoint if needed
    if idx % 50 == 0:
        with open("checkpoint.txt", "w") as f:
            f.write(str(idx))

    # Simulate time between transactions
    sleep_time = df.iloc[idx+1]["unix_time"] - df.iloc[idx]["unix_time"]
    time.sleep(sleep_time)
