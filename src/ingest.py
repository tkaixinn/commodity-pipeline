import yfinance as yf
import pandas as pd

TICKERS = {
    "CL=F": "Crude Oil",
    "GC=F": "Gold",
    "NG=F": "Natural Gas",
}

def fetch_commodity_data(period="5d"):
    """
    Pulls historical price data for each ticker in TICKERS.
    Returns a single combined DataFrame.
    """
    all_data = []

    for ticker in TICKERS:
        df = yf.Ticker(ticker).history(period=period)
        df = df.reset_index()
        df["ticker"] = ticker
        all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)
    return combined