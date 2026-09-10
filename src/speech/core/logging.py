import logging

from speech.core.config import get_settings


def configure_logging() -> None:
    """Configure application logging."""

    settings = get_settings()

    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
