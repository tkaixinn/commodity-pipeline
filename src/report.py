import os
import json
import logging
import boto3

from ingest import TICKERS

logger = logging.getLogger(__name__)

def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))

def build_ticker_facts(cleaned):
    facts = []
    for ticker in cleaned["ticker"].unique():
        rows = cleaned[cleaned["ticker"] == ticker].sort_values("price_date")
        first_close = float(rows.iloc[0]["close"])
        last_close = float(rows.iloc[-1]["close"])
        change_pct = (last_close - first_close) / first_close * 100
        facts.append({
            "commodity": TICKERS.get(ticker, ticker),
            "ticker": ticker,
            "trading_days": len(rows),
            "first_date": str(rows.iloc[0]["price_date"]),
            "last_date": str(rows.iloc[-1]["price_date"]),
            "last_close": round(last_close, 2),
            "change_pct_over_window": round(change_pct, 2),
        })
    return facts

def generate_report(model_id, quality_summary, ticker_facts):
    prompt = (
        "You are writing a short daily status note for a commodity price data pipeline.\n"
        "Use ONLY the numbers in the JSON below. Do not add any other figures or explanations "
        "for why prices moved.\n"
        "Write 3 short sections in markdown: Data quality, Price moves, Anything to check.\n"
        "Under 150 words.\n\n"
        f"Data quality summary:\n{json.dumps(quality_summary)}\n\n"
        f"Per-commodity facts:\n{json.dumps(ticker_facts)}\n"
    )
    response = get_bedrock_client().converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 400},
    )
    text = ""
    for block in response["output"]["message"]["content"]:
        if "text" in block:
            text = block["text"]
            break
    logger.info(f"Bedrock report generated ({len(text)} chars)")
    return text