import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_commodity_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    summary = {}

    df = df.rename(columns={
        "Date": "price_date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    })

    df = df[["ticker", "price_date", "open", "high", "low", "close", "volume"]]
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date

    total_rows = len(df)
    summary["total_rows_received"] = total_rows

    # Check 1: missing critical price data
    missing_price_mask = df[["open", "high", "low", "close"]].isna().any(axis=1)
    summary["rows_missing_price_data"] = int(missing_price_mask.sum())
    df = df[~missing_price_mask]

    # Check 2: negative or zero prices (invalid for commodities)
    invalid_price_mask = (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
    summary["rows_with_invalid_prices"] = int(invalid_price_mask.sum())
    df = df[~invalid_price_mask]

    # Check 3: duplicate ticker+date combos
    duplicate_mask = df.duplicated(subset=["ticker", "price_date"])
    summary["duplicate_rows_dropped"] = int(duplicate_mask.sum())
    df = df[~duplicate_mask]

    summary["total_rows_clean"] = len(df)
    summary["rows_dropped_total"] = total_rows - len(df)

    logger.info(
        f"Data quality summary: received={summary['total_rows_received']}, "
        f"clean={summary['total_rows_clean']}, "
        f"dropped_missing_price={summary['rows_missing_price_data']}, "
        f"dropped_invalid_price={summary['rows_with_invalid_prices']}, "
        f"dropped_duplicates={summary['duplicate_rows_dropped']}"
    )

    return df, summary