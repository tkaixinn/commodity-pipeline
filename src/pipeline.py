import logging
from ingest import fetch_commodity_data
from transform import clean_commodity_data
from load import load_commodity_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def run_pipeline():
    logger.info("Step 1: Fetching data from yfinance...")
    raw = fetch_commodity_data()
    logger.info(f"Fetched {len(raw)} raw rows")

    logger.info("Step 2: Cleaning/transforming data...")
    cleaned, quality_summary = clean_commodity_data(raw)
    logger.info(f"{len(cleaned)} rows after cleaning")

    logger.info("Step 3: Loading into Postgres...")
    load_commodity_data(cleaned)

    logger.info("Pipeline run complete.")
    logger.info(f"Final data quality summary: {quality_summary}")

if __name__ == "__main__":
    run_pipeline()