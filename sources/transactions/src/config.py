"""Configuration settings for the event producer."""
import os
from pathlib import Path

# Kafka configuration
# Use environment variable if set, otherwise default to Docker service name
# For local development, set KAFKA_BROKER=localhost:9092
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
KAFKA_RETRY_DELAY = int(os.getenv("KAFKA_RETRY_DELAY", "2"))  # seconds
KAFKA_MAX_RETRIES = int(os.getenv("KAFKA_MAX_RETRIES", "10"))

# File paths
CHECKPOINT_FILE = Path("checkpoint.txt")
EVENTS_CSV_FILE = Path("credit_card_transactions_events.csv")

# Processing configuration
CHECKPOINT_INTERVAL = 50  # Save checkpoint every N events

# Exchange rates to USD
EXCHANGE_RATES = {
    "EUR": 1.17,
    "DKK": 0.16,
    "SEK": 0.11,
    "NOK": 0.10,
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
