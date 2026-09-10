import logging
from functools import lru_cache

from faster_whisper import WhisperModel

from speech.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_whisper_model() -> WhisperModel:
    """Load and cache the Whisper model."""

    settings = get_settings()

    logger.info(
        "Loading Whisper model: model=%s device=%s compute_type=%s",
        settings.model_name,
        settings.device,
        settings.compute_type,
    )

    return WhisperModel(
        settings.model_name,
        device=settings.device,
        compute_type=settings.compute_type,
    )
