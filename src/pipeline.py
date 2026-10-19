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
from report import build_ticker_facts, generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def archive_to_s3(bucket, run_time, raw, cleaned, quality_summary, model_id=None):
    day = run_time.strftime("%Y-%m-%d")
    stamp = run_time.strftime("%Y%m%dT%H%M%SZ")

    upload_text(bucket, f"raw/{day}/{stamp}.csv", raw.to_csv(index=False), "text/csv")
    upload_text(bucket, f"clean/{day}/{stamp}.csv", cleaned.to_csv(index=False), "text/csv")
    upload_text(bucket, f"summaries/{day}/{stamp}.json", json.dumps(quality_summary), "application/json")

    # NEW: plain-English report written by Bedrock (skipped if BEDROCK_MODEL_ID isn't set)
    if model_id:
        facts = build_ticker_facts(cleaned)
        report_text = generate_report(model_id, quality_summary, facts)
        upload_text(bucket, f"reports/{day}/{stamp}.md", report_text, "text/markdown")

def run_pipeline():
    run_time = datetime.now(timezone.utc)
    bucket = os.getenv("S3_BUCKET")
    model_id = os.getenv("BEDROCK_MODEL_ID")  # NEW
    aws_ok = True  # CHANGED: was s3_ok, now covers S3 and Bedrock

    logger.info("Step 1: Fetching data from yfinance...")
    raw = fetch_commodity_data()
    logger.info(f"Fetched {len(raw)} raw rows")

    logger.info("Step 2: Cleaning/transforming data...")
    cleaned, quality_summary = clean_commodity_data(raw)
    logger.info(f"{len(cleaned)} rows after cleaning")

    if bucket:
        logger.info("Step 3: Archiving to S3...")
        try:
            archive_to_s3(bucket, run_time, raw, cleaned, quality_summary, model_id)  # CHANGED: passes model_id
        except (BotoCoreError, ClientError):
            logger.exception("AWS step failed, continuing with the Postgres load")  # CHANGED: wording
            aws_ok = False
    else:
        logger.info("S3_BUCKET not set, skipping S3 archive")

    logger.info("Step 4: Loading into Postgres...")
    load_commodity_data(cleaned)

    logger.info("Pipeline run complete.")
    logger.info(f"Final data quality summary: {quality_summary}")

    if not aws_ok:
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()