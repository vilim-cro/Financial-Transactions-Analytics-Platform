"""Configuration settings for FX rates ingestion."""
import os

# FreeCurrencyAPI configuration
FREECURRENCYAPI_API_KEY = os.getenv("FREECURRENCYAPI_API_KEY", "fca_live_ELNmWqgUPubg76NaexnWUpXv6Cmn2P55Piqo7Ukt")

# Google Cloud Storage configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "financial_transaction_events")
# Path to service account JSON file (optional, can also use default credentials)
# Treat empty string as unset so we use default path (avoids "File was not found" from google.auth)
GOOGLE_APPLICATION_CREDENTIALS = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip() or "credentials/composite-rune-478908-j1-3abb9d5ebc37.json"

# Currencies to fetch
CURRENCIES = ["EUR", "DKK", "NOK", "SEK"]

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
