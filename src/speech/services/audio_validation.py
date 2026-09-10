from pathlib import Path

import av


class InvalidAudioError(ValueError):
    """Raised when an uploaded file is not valid audio."""


def validate_audio_file(audio_path: Path) -> None:
    """Verify that a file can be opened and contains audio."""

    try:
        container = av.open(str(audio_path))
    except Exception as exc:
        raise InvalidAudioError("Uploaded file is not a valid audio file.") from exc

    try:
        has_audio_stream = any(stream.type == "audio" for stream in container.streams)

        if not has_audio_stream:
            raise InvalidAudioError("Uploaded file does not contain an audio stream.")

    finally:
        container.close()
