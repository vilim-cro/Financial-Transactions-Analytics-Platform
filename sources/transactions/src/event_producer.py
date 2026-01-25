"""Event producer for streaming credit card transactions to Kafka."""
import json
import logging
import random
import time
from typing import Dict

import pandas as pd
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError

from config import (
    CHECKPOINT_FILE,
    CHECKPOINT_INTERVAL,
    EVENTS_CSV_FILE,
    EXCHANGE_RATES,
    KAFKA_BROKER,
    KAFKA_MAX_RETRIES,
    KAFKA_RETRY_DELAY,
    KAFKA_TOPIC,
    LOG_FORMAT,
    LOG_LEVEL,
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
)
logger = logging.getLogger(__name__)


def connect_kafka(retries: int = KAFKA_MAX_RETRIES, delay: int = KAFKA_RETRY_DELAY) -> KafkaProducer:
    """
    Connect to Kafka broker with retry logic.
    
    Args:
        retries: Maximum number of connection attempts
        delay: Delay between retry attempts in seconds
        
    Returns:
        KafkaProducer instance
        
    Raises:
        ConnectionError: If unable to connect after all retries
    """
    attempt = 0
    while attempt < retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            logger.info("Successfully connected to Kafka broker at %s", KAFKA_BROKER)
            return producer
        except Exception as e:
            attempt += 1
            if attempt < retries:
                logger.warning(
                    "Kafka not ready (attempt %d/%d). Retrying in %ds... Error: %s",
                    attempt,
                    retries,
                    delay,
                    e,
                )
                time.sleep(delay)
    logger.error("Failed to connect to Kafka after %d attempts", retries)
    raise ConnectionError(f"Failed to connect to Kafka after {retries} attempts")
    


def load_checkpoint(checkpoint_file: Path) -> int:
    """
    Load the last processed index from checkpoint file.
    
    Args:
        checkpoint_file: Path to checkpoint file
        
    Returns:
        Last processed index (0 if file doesn't exist or is empty)
    """
    if not checkpoint_file.exists():
        logger.info("Checkpoint file not found, starting from beginning")
        return 0
    
    try:
        with open(checkpoint_file, "r") as f:
            content = f.read().strip()
            if not content:
                logger.info("Checkpoint file is empty, starting from beginning")
                return 0
            last_idx = int(content)
            logger.info("Resuming from checkpoint at index %d", last_idx)
            return last_idx
    except (ValueError, IOError) as e:
        logger.warning("Error reading checkpoint file: %s. Starting from beginning", e)
        return 0


def save_checkpoint(checkpoint_file: Path, index: int) -> None:
    """
    Save the current index to checkpoint file.
    
    Args:
        checkpoint_file: Path to checkpoint file
        index: Current index to save
    """
    try:
        with open(checkpoint_file, "w") as f:
            f.write(str(index))
    except IOError as e:
        logger.error("Failed to save checkpoint: %s", e)


def transform_event(event: pd.Series, exchange_rates: Dict[str, float]) -> Dict:
    """
    Transform a transaction event by adding currency conversion.
    
    Args:
        event: Pandas Series containing transaction data
        exchange_rates: Dictionary mapping currency codes to USD exchange rates
        
    Returns:
        Dictionary with transformed event data (without usd_amt)
    """
    currency = random.choice(list(exchange_rates.keys()))
    original_amt = event["usd_amt"] / exchange_rates[currency]
    
    # Create a copy to avoid modifying the original
    event_dict = event.to_dict()
    event_dict["original_amt"] = original_amt
    event_dict["currency"] = currency
    # Remove usd_amt as it's replaced by original_amt
    del event_dict["usd_amt"]
    
    return event_dict


def calculate_sleep_time(df: pd.DataFrame, current_idx: int) -> float:
    """
    Calculate sleep time between transactions based on timestamps.
    
    Args:
        df: DataFrame containing transaction data
        current_idx: Current transaction index
        
    Returns:
        Sleep time in seconds (0 if at end of dataframe)
    """
    if current_idx + 1 >= len(df):
        return 0.0
    
    return max(0.0, df.iloc[current_idx + 1]["unix_time"] - df.iloc[current_idx]["unix_time"])


def main() -> None:
    """Main function to process and stream transactions."""
    # Connect to Kafka
    producer = connect_kafka()
    
    # Load transaction data
    if not EVENTS_CSV_FILE.exists():
        logger.error("Events CSV file not found: %s", EVENTS_CSV_FILE)
        raise FileNotFoundError(f"Events CSV file not found: {EVENTS_CSV_FILE}")
    
    df = pd.read_csv(EVENTS_CSV_FILE, sep=";")
    df.rename(columns={"amt": "usd_amt"}, inplace=True)
    logger.info("Loaded %d transactions from CSV", len(df))
    
    # Load checkpoint
    last_idx = load_checkpoint(CHECKPOINT_FILE)
    
    # Initialize idx to last_idx in case of early error
    idx = last_idx
    
    # Process transactions
    try:
        for idx in range(last_idx, len(df)):
            event = df.iloc[idx]
            
            # Transform event with currency conversion
            transformed_event = transform_event(event, EXCHANGE_RATES)
            
            # Log and send to Kafka
            logger.debug("Processing transaction %d/%d", idx + 1, len(df))
            print(transformed_event, flush=True)
            
            try:
                producer.send(KAFKA_TOPIC, transformed_event)
                producer.flush()
            except KafkaError as e:
                logger.error("Failed to send message to Kafka: %s", e)
                # Continue processing even if Kafka send fails
            
            # Save checkpoint periodically
            if (idx + 1) % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(CHECKPOINT_FILE, idx + 1)
                logger.info("Checkpoint saved at index %d", idx + 1)
            
            # Simulate time between transactions
            sleep_time = calculate_sleep_time(df, idx)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Save final checkpoint
        save_checkpoint(CHECKPOINT_FILE, len(df))
        logger.info("Finished processing all %d transactions", len(df))
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user, saving checkpoint...")
        save_checkpoint(CHECKPOINT_FILE, idx)
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        save_checkpoint(CHECKPOINT_FILE, idx)
        raise
    finally:
        producer.close()
        logger.info("Kafka producer closed")


if __name__ == "__main__":
    main()
