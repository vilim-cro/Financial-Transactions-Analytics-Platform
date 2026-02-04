"""GCS upload for transaction events: credential resolution and Parquet batch upload."""
import io
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account

from config import GOOGLE_APPLICATION_CREDENTIALS


def get_gcs_client() -> Optional[storage.Client]:
    """
    Create a GCS client using GOOGLE_APPLICATION_CREDENTIALS.
    Resolves relative paths (e.g. credentials/file.json) against /app/credentials and /app.
    Returns None if credentials are not set or file not found (caller can skip upload).
    """
    if not (GOOGLE_APPLICATION_CREDENTIALS or "").strip():
        return None
    creds_path = Path(GOOGLE_APPLICATION_CREDENTIALS.strip())
    if not creds_path.is_absolute():
        for base in [
            Path("/app/credentials") / creds_path.name,
            Path("/app") / creds_path,
            Path("/app/credentials") / creds_path,
        ]:
            if base.exists() and base.is_file():
                creds_path = base
                break
        else:
            # Try project root (for local dev)
            root = Path(__file__).resolve().parent.parent.parent.parent
            candidate = root / creds_path
            if candidate.exists() and candidate.is_file():
                creds_path = candidate
            elif not creds_path.exists():
                return None
    if creds_path.is_dir():
        json_files = list(creds_path.glob("*.json"))
        if len(json_files) == 1:
            creds_path = json_files[0]
        elif len(json_files) != 1:
            return None
    if not (creds_path.exists() and creds_path.is_file()):
        return None
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
    credentials = service_account.Credentials.from_service_account_file(
        str(creds_path)
    )
    return storage.Client(credentials=credentials)


def upload_transactions_batch(
    client: storage.Client,
    bucket_name: str,
    events: list[dict],
    batch_index: int = 0,
) -> None:
    """
    Upload a batch of transaction events to GCS as a single Parquet file under
    transactions/YYYY-MM-DD/YYYY-MM-DDTHH-mm-ss_<batch_index>.parquet.
    """
    if not events:
        return
    now = datetime.utcnow()
    date_part = now.strftime("%Y-%m-%d")
    datetime_part = now.strftime("%Y-%m-%dT%H-%M-%S")
    blob_name = f"transactions/{date_part}/{datetime_part}_{batch_index}.parquet"
    df = pd.DataFrame(events)
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, engine="pyarrow", index=False)
    parquet_data = parquet_buffer.getvalue()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        parquet_data,
        content_type="application/octet-stream",
    )
