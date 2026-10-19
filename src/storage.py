import os
import logging
import boto3

logger = logging.getLogger(__name__)

def get_s3_client():
    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))

def upload_text(bucket, key, text, content_type):
    client = get_s3_client()
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=text.encode("utf-8"),
        ContentType=content_type,
    )
    logger.info(f"Uploaded s3://{bucket}/{key} ({len(text)} chars)")