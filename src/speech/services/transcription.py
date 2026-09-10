import logging
from pathlib import Path
from time import perf_counter
from typing import Any

from speech.core.config import get_settings
from speech.models.whisper import load_whisper_model

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: Path) -> dict[str, Any]:
    """Transcribe an audio file and return structured results."""

    if not audio_path.exists():
        logger.error("Audio file not found: %s", audio_path)

        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    settings = get_settings()
    model = load_whisper_model()

    logger.info(
        "Starting transcription: file=%s",
        audio_path.name,
    )

    start_time = perf_counter()

    try:
        segments, info = model.transcribe(
            str(audio_path),
            beam_size=settings.beam_size,
            language=settings.language,
        )

        transcription_segments = []
        text_parts = []

        for segment in segments:
            text = segment.text.strip()

            if not text:
                continue

            transcription_segments.append(
                {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": text,
                }
            )

            text_parts.append(text)

    except Exception:
        logger.exception(
            "Transcription failed: file=%s",
            audio_path.name,
        )
        raise

    processing_time = perf_counter() - start_time

    result = {
        "text": " ".join(text_parts),
        "language": info.language,
        "language_probability": round(
            info.language_probability,
            4,
        ),
        "duration": round(info.duration, 2),
        "segments": transcription_segments,
    }

    logger.info(
        "Transcription completed: file=%s language=%s "
        "duration=%.2fs processing_time=%.2fs",
        audio_path.name,
        info.language,
        info.duration,
        processing_time,
    )

    return result
