"""Configuration settings for the event consumer."""
import os

# Kafka configuration
# Use environment variable if set, otherwise default to Docker service name
# For local development, set KAFKA_BROKER=localhost:9092
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "transactions-consumer-group")
KAFKA_RETRY_DELAY = float(os.getenv("KAFKA_RETRY_DELAY", "2"))  # seconds
# Set to 0 to retry forever
KAFKA_MAX_RETRIES = int(os.getenv("KAFKA_MAX_RETRIES", "0"))

# GCS configuration (optional: if unset, consumer is log-only)
GCS_BUCKET_NAME = (os.getenv("GCS_BUCKET_NAME") or "").strip()
GOOGLE_APPLICATION_CREDENTIALS = (
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or ""
).strip() or "credentials/composite-rune-478908-j1-3abb9d5ebc37.json"
# Flush buffer to GCS when this many seconds have passed since last flush (default 10 min)
GCS_FLUSH_SECONDS = float(os.getenv("GCS_FLUSH_SECONDS", "600"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
