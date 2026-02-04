"""Event consumer for consuming and logging credit card transactions from Kafka."""
import json
import logging
import signal
import sys
import time
from typing import Any, Dict, List, Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from config import (
    GCS_BUCKET_NAME,
    GCS_FLUSH_SECONDS,
    KAFKA_BROKER,
    KAFKA_CONSUMER_GROUP,
    KAFKA_MAX_RETRIES,
    KAFKA_RETRY_DELAY,
    KAFKA_TOPIC,
    LOG_FORMAT,
    LOG_LEVEL,
)
from gcs_upload import get_gcs_client, upload_transactions_batch

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
)
logger = logging.getLogger(__name__)

# Global consumer for graceful shutdown
consumer: Optional[KafkaConsumer] = None
# GCS batching: buffer and last flush time (only used when GCS is enabled)
gcs_client: Optional[Any] = None
gcs_bucket_name: str = ""
event_buffer: List[Dict[str, Any]] = []
last_flush_time: float = 0.0
flush_counter: int = 0


def flush_gcs_buffer() -> None:
    """Flush buffered events to GCS if client is configured and buffer is non-empty."""
    global event_buffer, last_flush_time, flush_counter
    if not gcs_client or not gcs_bucket_name or not event_buffer:
        return
    try:
        upload_transactions_batch(gcs_client, gcs_bucket_name, event_buffer, flush_counter)
        logger.info("Flushed %d events to GCS", len(event_buffer))
        event_buffer = []
        flush_counter += 1
        last_flush_time = time.time()
    except Exception as e:
        logger.error("GCS upload failed (buffer kept for next flush): %s", e, exc_info=True)


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, closing consumer...")
    flush_gcs_buffer()
    if consumer:
        consumer.close()
    sys.exit(0)


def connect_kafka() -> KafkaConsumer:
    """
    Connect to Kafka broker and create a consumer.
    
    Returns:
        KafkaConsumer instance
        
    Raises:
        ConnectionError: If unable to connect to Kafka
    """
    attempt = 0
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                group_id=KAFKA_CONSUMER_GROUP,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",  # Start from beginning if no offset
                enable_auto_commit=True,
            )
            logger.info(
                "Connected to Kafka at %s (topic=%s, group=%s)",
                KAFKA_BROKER,
                KAFKA_TOPIC,
                KAFKA_CONSUMER_GROUP,
            )
            return consumer
        except Exception as e:
            attempt += 1
            if KAFKA_MAX_RETRIES and attempt >= KAFKA_MAX_RETRIES:
                logger.error("Failed to connect to Kafka after %d attempts: %s", attempt, e)
                raise ConnectionError(f"Failed to connect to Kafka after {attempt} attempts: {e}") from e

            logger.warning(
                "Kafka not ready (attempt %d%s). Retrying in %.1fs... Error: %s",
                attempt,
                f"/{KAFKA_MAX_RETRIES}" if KAFKA_MAX_RETRIES else "",
                KAFKA_RETRY_DELAY,
                e,
            )
            time.sleep(KAFKA_RETRY_DELAY)


def log_event(event: Dict) -> None:
    """
    Log a transaction event with formatted output.
    
    Args:
        event: Dictionary containing transaction event data
    """
    logger.info("=" * 80)
    logger.info("Received Transaction Event:")
    logger.info("-" * 80)
    
    # Log key fields with formatting
    if "trans_date_trans_time" in event:
        logger.info("Timestamp: %s", event["trans_date_trans_time"])
    if "user_id" in event:
        logger.info("User ID: %s", event["user_id"])
    if "merchant" in event:
        logger.info("Merchant: %s", event["merchant"])
    if "category" in event:
        logger.info("Category: %s", event["category"])
    if "original_amt" in event:
        logger.info("Amount: %.2f %s", event["original_amt"], event.get("currency", "USD"))
    if "is_fraud" in event:
        logger.info("Fraud Flag: %s", event["is_fraud"])
    
    # Log full event as JSON for debugging
    logger.debug("Full event data: %s", json.dumps(event, indent=2, default=str))
    logger.info("=" * 80)


def main() -> None:
    """Main function to consume and log transactions."""
    global consumer, gcs_client, gcs_bucket_name, event_buffer, last_flush_time
    # Optional GCS: init client and bucket if configured
    if GCS_BUCKET_NAME:
        gcs_client = get_gcs_client()
        gcs_bucket_name = GCS_BUCKET_NAME
        if gcs_client:
            logger.info("GCS upload enabled: bucket=%s, flush every %s s", gcs_bucket_name, GCS_FLUSH_SECONDS)
        else:
            logger.warning("GCS bucket set but credentials not available; GCS upload disabled")
            gcs_bucket_name = ""
    last_flush_time = time.time()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Connect to Kafka
    try:
        consumer = connect_kafka()
    except ConnectionError as e:
        logger.error("Failed to establish Kafka connection: %s", e)
        sys.exit(1)

    logger.info("Starting to consume messages from topic '%s'...", KAFKA_TOPIC)
    logger.info("Press Ctrl+C to stop")

    try:
        for message in consumer:
            try:
                event = message.value
                log_event(event)
                if gcs_client and gcs_bucket_name:
                    event_buffer.append(event)
                    if time.time() - last_flush_time >= GCS_FLUSH_SECONDS:
                        flush_gcs_buffer()
            except (KeyError, ValueError, TypeError) as e:
                logger.error("Error processing message: %s. Message: %s", e, message.value)
            except KafkaError as e:
                logger.error("Kafka error while processing message: %s", e)
            except Exception as e:
                logger.error("Unexpected error processing message: %s", e, exc_info=True)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Unexpected error in consumer loop: %s", e, exc_info=True)
    finally:
        flush_gcs_buffer()
        logger.info("Closing consumer...")
        consumer.close()
        logger.info("Consumer closed")


if __name__ == "__main__":
    main()
