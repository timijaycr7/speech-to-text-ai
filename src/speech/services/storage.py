from pathlib import Path

import boto3

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
