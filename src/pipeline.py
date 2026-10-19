import json
import logging
import os
import sys
from datetime import datetime, timezone

from botocore.exceptions import BotoCoreError, ClientError

from ingest import fetch_commodity_data
from transform import clean_commodity_data
from load import load_commodity_data
from storage import upload_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def archive_to_s3(bucket, run_time, raw, cleaned, quality_summary):
    day = run_time.strftime("%Y-%m-%d")
    stamp = run_time.strftime("%Y%m%dT%H%M%SZ")

    upload_text(bucket, f"raw/{day}/{stamp}.csv", raw.to_csv(index=False), "text/csv")
    upload_text(bucket, f"clean/{day}/{stamp}.csv", cleaned.to_csv(index=False), "text/csv")
    upload_text(bucket, f"summaries/{day}/{stamp}.json", json.dumps(quality_summary), "application/json")

def run_pipeline():
    run_time = datetime.now(timezone.utc)
    bucket = os.getenv("S3_BUCKET")
    s3_ok = True

    logger.info("Step 1: Fetching data from yfinance...")
    raw = fetch_commodity_data()
    logger.info(f"Fetched {len(raw)} raw rows")

    logger.info("Step 2: Cleaning/transforming data...")
    cleaned, quality_summary = clean_commodity_data(raw)
    logger.info(f"{len(cleaned)} rows after cleaning")

    # NEW: archive raw + clean + summary to S3 (skipped if S3_BUCKET isn't set)
    if bucket:
        logger.info("Step 3: Archiving to S3...")
        try:
            archive_to_s3(bucket, run_time, raw, cleaned, quality_summary)
        except (BotoCoreError, ClientError):
            logger.exception("S3 archive failed, continuing with the Postgres load")
            s3_ok = False
    else:
        logger.info("S3_BUCKET not set, skipping S3 archive")

    logger.info("Step 4: Loading into Postgres...")  # CHANGED: was Step 3
    load_commodity_data(cleaned)

    logger.info("Pipeline run complete.")
    logger.info(f"Final data quality summary: {quality_summary}")

    # NEW: exit non-zero so a failed S3 archive shows up as a failed run
    if not s3_ok:
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()