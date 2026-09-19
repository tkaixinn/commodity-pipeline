import pandas as pd

def clean_commodity_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and validates raw commodity price data before loading into Postgres.
    """
    df = df.copy()

    # Rename columns to match Postgres schema
    df = df.rename(columns={
        "Date": "price_date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    })

    # Keep only the columns we actually need
    df = df[["ticker", "price_date", "open", "high", "low", "close", "volume"]]

    # Convert price_date to plain date (drop time/timezone info)
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date

    # Data quality checks
    before = len(df)
    df = df.dropna(subset=["open", "high", "low", "close"])  # drop rows missing critical price data
    df = df.drop_duplicates(subset=["ticker", "price_date"])  # avoid duplicate rows
    after = len(df)

    if before != after:
        print(f"Data quality check: dropped {before - after} invalid/duplicate rows")

    return df