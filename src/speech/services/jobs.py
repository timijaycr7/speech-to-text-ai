from pathlib import Path
from uuid import uuid4

from speech.services.queue import enqueue_transcription
from speech.services.storage import upload_audio


def create_transcription_job(
    audio_path: Path,
    original_filename: str,
) -> dict[str, str]:
    """Upload audio and enqueue a transcription job."""

    job_id = str(uuid4())

    suffix = Path(original_filename).suffix.lower()

    s3_key = f"uploads/{job_id}/input{suffix}"

    upload_audio(
        audio_path=audio_path,
        object_key=s3_key,
    )

    enqueue_transcription(
        job_id=job_id,
        s3_key=s3_key,
    )

    return {
        "job_id": job_id,
        "status": "queued",
    }
