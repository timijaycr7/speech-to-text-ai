import logging
import tempfile
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile

from speech.api.schemas import TranscriptionResponse
from speech.core.config import get_settings
from speech.core.logging import configure_logging
from speech.services.audio_validation import (
    InvalidAudioError,
    validate_audio_file,
)
from speech.services.transcription import transcribe_audio

configure_logging()

app = FastAPI(
    title="Speech-to-Text API",
    description="Production-oriented speech-to-text API powered by Whisper.",
    version="0.1.0",
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())

    logger.info(
        "Request started: request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "Request completed: request_id=%s status_code=%s",
        request_id,
        response.status_code,
    )

    return response


ALLOWED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
    ".ogg",
    ".webm",
}
CHUNK_SIZE = 1024 * 1024


def save_upload_with_limit(
    file: UploadFile,
    destination,
) -> None:
    """Save an uploaded file while enforcing a size limit."""

    settings = get_settings()

    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    total_bytes = 0

    while True:
        chunk = file.file.read(CHUNK_SIZE)

        if not chunk:
            break

        total_bytes += len(chunk)

        if total_bytes > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File too large. Maximum size is {settings.max_upload_size_mb} MB."
                ),
            )

        destination.write(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio file is empty.",
        )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/api/v1/transcriptions",
    response_model=TranscriptionResponse,
)
def create_transcription(
    file: Annotated[UploadFile, File(...)],
) -> TranscriptionResponse:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio file must have a filename.",
        )

    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {suffix}",
        )

    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            save_upload_with_limit(
                file,
                temp_file,
            )

        temp_path = Path(temp_file.name)

        validate_audio_file(temp_path)

        result = transcribe_audio(temp_path)

        return TranscriptionResponse.model_validate(result)

    except HTTPException:
        raise

    except InvalidAudioError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Transcription failed.",
        ) from exc

    finally:
        file.file.close()

        if temp_path and temp_path.exists():
            temp_path.unlink()


logger = logging.getLogger(__name__)
