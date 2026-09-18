import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def load_commodity_data(df):
    """
    Upserts commodity price rows into Postgres.
    Uses ON CONFLICT to avoid duplicate rows on re-run.
    """
    conn = get_connection()
    cur = conn.cursor()

    insert_query = """
        INSERT INTO commodity_prices (ticker, price_date, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker, price_date)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            ingested_at = NOW();
    """

    rows = list(df[["ticker", "price_date", "open", "high", "low", "close", "volume"]].itertuples(index=False, name=None))

    cur.executemany(insert_query, rows)
    conn.commit()

    print(f"Loaded/updated {len(rows)} rows into commodity_prices")

    cur.close()
    conn.close()

if __name__ == "__main__":
    from ingest import fetch_commodity_data
    from transform import clean_commodity_data

    raw = fetch_commodity_data()
    cleaned = clean_commodity_data(raw)
    load_commodity_data(cleaned)