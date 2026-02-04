"""Fetch FX rates and upload to Google Cloud Storage."""
import os
import io
from pathlib import Path
from datetime import datetime
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
import freecurrencyapi
from config import (
    FREECURRENCYAPI_API_KEY,
    GCS_BUCKET_NAME,
    GOOGLE_APPLICATION_CREDENTIALS,
    CURRENCIES
)


def get_fx_rates() -> dict:
    """Fetch latest FX rates from the API."""
    if not FREECURRENCYAPI_API_KEY:
        raise ValueError("FREECURRENCYAPI_API_KEY environment variable is required")
    
    client = freecurrencyapi.Client(FREECURRENCYAPI_API_KEY)
    result = client.latest(currencies=CURRENCIES)["data"]
    return result


def upload_to_gcs(df: pd.DataFrame, bucket_name: str, blob_name: str) -> None:
    """Upload data to Google Cloud Storage as Parquet."""
    # Initialize GCS client with credentials
    credentials = None
    
    print(f"DEBUG: GOOGLE_APPLICATION_CREDENTIALS env var = {GOOGLE_APPLICATION_CREDENTIALS}")
    print(f"DEBUG: Current working directory = {os.getcwd()}")
    print(f"DEBUG: __file__ location = {__file__}")
    
    if GOOGLE_APPLICATION_CREDENTIALS:
        # Resolve path (handle both absolute and relative paths)
        creds_path = Path(GOOGLE_APPLICATION_CREDENTIALS)
        print(f"DEBUG: Initial creds_path = {creds_path}")
        print(f"DEBUG: creds_path.is_absolute() = {creds_path.is_absolute()}")
        
        if creds_path.is_absolute():
            # Already absolute path (e.g., /app/credentials/file.json)
            print(f"DEBUG: Using absolute path: {creds_path}")
        else:
            # If relative, try multiple locations
            print(f"DEBUG: Path is relative, trying to resolve...")
            possible_paths = [
                Path("/app/credentials") / creds_path.name,  # Just filename in mounted folder
                Path("/app") / creds_path,  # Full relative path from /app
                Path("/app/credentials") / creds_path,  # Relative path in credentials folder
                Path(__file__).parent.parent.parent.parent.parent / creds_path,  # Project root
            ]
            
            print(f"DEBUG: Trying possible paths:")
            for i, possible_path in enumerate(possible_paths):
                exists = possible_path.exists()
                print(f"  {i+1}. {possible_path} - exists: {exists}")
                if exists:
                    creds_path = possible_path
                    print(f"DEBUG: Found credentials at: {creds_path}")
                    break
        
        print(f"DEBUG: Final creds_path = {creds_path}")
        print(f"DEBUG: creds_path.exists() = {creds_path.exists()}")
        
        # List contents of /app/credentials if it exists
        creds_dir = Path("/app/credentials")
        if creds_dir.exists():
            print(f"DEBUG: /app/credentials directory exists")
            print(f"DEBUG: Contents of /app/credentials:")
            try:
                for item in creds_dir.iterdir():
                    print(f"  - {item.name} (is_file: {item.is_file()})")
            except Exception as e:
                print(f"  Error listing directory: {e}")
        else:
            print(f"DEBUG: /app/credentials directory does NOT exist")
        
        if creds_path.is_dir():
            # Path is a directory: use first .json file inside
            json_files = list(creds_path.glob("*.json"))
            if len(json_files) == 1:
                creds_path = json_files[0]
            elif len(json_files) > 1:
                raise FileNotFoundError(
                    f"Multiple JSON files in {creds_path}; set GOOGLE_APPLICATION_CREDENTIALS to the exact file path"
                )
            else:
                raise FileNotFoundError(f"No .json file found in {creds_path}")
        if creds_path.exists() and creds_path.is_file():
            # Set environment variable for Google client libraries
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path)
            )
            print(f"✓ Using credentials from: {creds_path}")
        else:
            print(f"✗ ERROR: Credentials file not found at {creds_path}")
            print(f"  Attempted path: {creds_path}")
            print(f"  Absolute: {creds_path.is_absolute()}")
            print(f"  Parent exists: {creds_path.parent.exists() if creds_path.parent else 'N/A'}")
            raise FileNotFoundError(f"Credentials file not found at {creds_path}")
    
    # Initialize client with credentials if available
    if credentials:
        client = storage.Client(credentials=credentials)
    else:
        # Try to use default credentials (for GCP environments or gcloud auth)
        # This will use GOOGLE_APPLICATION_CREDENTIALS env var if set
        client = storage.Client()
    
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    # Convert DataFrame to Parquet format in memory
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
    parquet_data = parquet_buffer.getvalue()
    
    # Upload with content type
    blob.upload_from_string(
        parquet_data,
        content_type='application/octet-stream'
    )
    print(f"Successfully uploaded to gs://{bucket_name}/{blob_name}")


def main() -> None:
    """Main function to fetch FX rates and upload to GCS."""
    if not GCS_BUCKET_NAME:
        raise ValueError("GCS_BUCKET_NAME environment variable is required")
    
    # Generate timestamped filename
    # Format: fx_rates/YYYY/MM/DD/fx_rates_YYYYMMDD_HHMMSS.parquet
    now = datetime.utcnow()
    date_path = now.strftime('%Y/%m/%d')
    blob_name = f"fx_rates/{date_path}/fx_rates_{now.strftime('%Y%m%d_%H%M%S')}.parquet"
    
    try:
        # Fetch FX rates
        print("Fetching FX rates...")
        fx_rates = get_fx_rates()
        
        # Convert to DataFrame format suitable for Parquet
        # Structure: timestamp, base_currency, currency, rate
        records = []
        timestamp = now.isoformat() + "Z"
        base_currency = "USD"
        
        for currency, rate in fx_rates.items():
            records.append({
                "timestamp": timestamp,
                "base_currency": base_currency,
                "currency": currency,
                "rate": float(rate)
            })
        
        df = pd.DataFrame(records)
        
        # Upload to GCS
        print(f"Uploading to GCS bucket: {GCS_BUCKET_NAME}")
        upload_to_gcs(df, GCS_BUCKET_NAME, blob_name)
        
        print("FX rates ingestion completed successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
