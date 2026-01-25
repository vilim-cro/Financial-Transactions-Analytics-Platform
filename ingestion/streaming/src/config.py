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

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
