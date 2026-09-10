import json
from pathlib import Path

from speech.core.logging import configure_logging
from speech.services.transcription import transcribe_audio


def main() -> None:
    configure_logging()

    audio_file = Path("data/sample.m4a")

    result = transcribe_audio(audio_file)

    print("\nTranscription result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
