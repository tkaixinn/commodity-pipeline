from ingest import fetch_commodity_data
from transform import clean_commodity_data
from load import load_commodity_data

def run_pipeline():
    print("Step 1: Fetching data from yfinance...")
    raw = fetch_commodity_data()
    print(f"Fetched {len(raw)} raw rows")

    print("\nStep 2: Cleaning/transforming data...")
    cleaned = clean_commodity_data(raw)
    print(f"{len(cleaned)} rows after cleaning")

    print("\nStep 3: Loading into Postgres...")
    load_commodity_data(cleaned)

    print("\nPipeline run complete.")

if __name__ == "__main__":
    run_pipeline()