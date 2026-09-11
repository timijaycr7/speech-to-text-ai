import json

import boto3

from speech.core.config import get_settings


def enqueue_transcription(
    job_id: str,
    s3_key: str,
) -> str:
    """Send a transcription job to Amazon SQS."""

    settings = get_settings()

    if not settings.sqs_queue_url:
        raise RuntimeError("STT_SQS_QUEUE_URL is not configured.")

    sqs = boto3.client(
        "sqs",
        region_name=settings.aws_region,
    )

    message = {
        "job_id": job_id,
        "s3_bucket": settings.s3_bucket,
        "s3_key": s3_key,
    }

    response = sqs.send_message(
        QueueUrl=settings.sqs_queue_url,
        MessageBody=json.dumps(message),
    )

    return response["MessageId"]
