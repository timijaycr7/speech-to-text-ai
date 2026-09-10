from pathlib import Path

import pytest

from speech.services.transcription import transcribe_audio


def test_missing_audio_file():
    audio_file = Path("does_not_exist.wav")

    with pytest.raises(FileNotFoundError):
        transcribe_audio(audio_file)


from types import SimpleNamespace


def test_transcription_result(monkeypatch, tmp_path):
    audio_file = tmp_path / "sample.wav"
    audio_file.touch()

    fake_segments = [
        SimpleNamespace(
            start=0.0,
            end=2.5,
            text="Hello world.",
        ),
        SimpleNamespace(
            start=2.5,
            end=5.0,
            text="This is a test.",
        ),
    ]

    fake_info = SimpleNamespace(
        language="en",
        language_probability=0.99,
        duration=5.0,
    )

    class FakeWhisperModel:
        def transcribe(self, audio_path, beam_size, language):
            return fake_segments, fake_info

    fake_model = FakeWhisperModel()

    monkeypatch.setattr(
        "speech.services.transcription.load_whisper_model",
        lambda: fake_model,
    )

    result = transcribe_audio(audio_file)

    assert result["text"] == "Hello world. This is a test."
    assert result["language"] == "en"
    assert result["duration"] == 5.0
    assert result["language_probability"] == 0.99

    assert len(result["segments"]) == 2

    assert result["segments"][0]["text"] == "Hello world."
    assert result["segments"][0]["start"] == 0.0
    assert result["segments"][0]["end"] == 2.5
