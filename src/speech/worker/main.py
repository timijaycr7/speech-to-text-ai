import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import boto3

from speech.core.config import get_settings
from speech.services.storage import (
    download_audio,
    upload_transcription_result,
)
from speech.services.transcription import transcribe_audio

logger = logging.getLogger(__name__)


def process_message(body: str) -> None:
    message = json.loads(body)

    job_id = message["job_id"]
    bucket = message["s3_bucket"]
    s3_key = message["s3_key"]

    settings = get_settings()

    if bucket != settings.s3_bucket:
        raise ValueError("Unexpected S3 bucket.")

    suffix = Path(s3_key).suffix

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = Path(temp_dir) / f"input{suffix}"

        logger.info(
            "Downloading audio for job %s",
            job_id,
        )

        download_audio(
            bucket=bucket,
            object_key=s3_key,
            destination=audio_path,
        )

        logger.info(
            "Transcribing job %s",
            job_id,
        )

        result = transcribe_audio(audio_path)

        upload_transcription_result(
            job_id=job_id,
            result=result,
        )

        logger.info(
            "Job %s completed successfully",
            job_id,
        )


def process_next_message(
    sqs: Any,
    queue_url: str,
) -> bool:
    """Receive and process one SQS message."""

    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20,
    )

    messages = response.get("Messages", [])

    if not messages:
        return False

    message = messages[0]

    try:
        process_message(message["Body"])

        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )

    except Exception:
        logger.exception("Failed to process transcription job.")

    return True


def run_worker() -> None:
    settings = get_settings()

    if not settings.sqs_queue_url:
        raise RuntimeError("STT_SQS_QUEUE_URL is not configured.")

    sqs = boto3.client(
        "sqs",
        region_name=settings.aws_region,
    )

    logger.info("Speech-to-text worker started.")

    while True:
        process_next_message(
            sqs=sqs,
            queue_url=settings.sqs_queue_url,
        )


if __name__ == "__main__":
    run_worker()
