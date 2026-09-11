import json
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from speech.core.config import get_settings


def upload_audio(audio_path: Path, object_key: str) -> str:
    """Upload an audio file to Amazon S3."""

    settings = get_settings()

    if not settings.s3_bucket:
        raise RuntimeError("STT_S3_BUCKET is not configured.")

    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
    )

    s3.upload_file(
        str(audio_path),
        settings.s3_bucket,
        object_key,
    )

    return f"s3://{settings.s3_bucket}/{object_key}"


def download_audio(
    bucket: str,
    object_key: str,
    destination: Path,
) -> None:
    """Download an audio file from Amazon S3."""

    settings = get_settings()

    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
    )

    s3.download_file(
        bucket,
        object_key,
        str(destination),
    )


def upload_transcription_result(
    job_id: str,
    result: dict[str, Any],
) -> str:
    """Upload a transcription result to Amazon S3."""

    settings = get_settings()

    if not settings.s3_bucket:
        raise RuntimeError("STT_S3_BUCKET is not configured.")

    object_key = f"results/{job_id}.json"

    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
    )

    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=object_key,
        Body=json.dumps(result),
        ContentType="application/json",
    )

    return f"s3://{settings.s3_bucket}/{object_key}"


def get_transcription_result(
    job_id: str,
) -> dict[str, Any] | None:
    """Return a completed transcription result from S3."""

    settings = get_settings()

    if not settings.s3_bucket:
        raise RuntimeError("STT_S3_BUCKET is not configured.")

    object_key = f"results/{job_id}.json"

    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
    )

    try:
        response = s3.get_object(
            Bucket=settings.s3_bucket,
            Key=object_key,
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")

        if error_code in {"NoSuchKey", "404", "NotFound"}:
            return None

        raise

    body = response["Body"].read()

    return json.loads(body.decode("utf-8"))
