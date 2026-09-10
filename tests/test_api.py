from fastapi.testclient import TestClient

from speech.api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_reject_unsupported_file():
    response = client.post(
        "/api/v1/transcriptions",
        files={
            "file": (
                "document.pdf",
                b"fake content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported audio format: .pdf"}


def test_create_transcription(monkeypatch):
    fake_result = {
        "text": "Hello, this is a test.",
        "language": "en",
        "language_probability": 1.0,
        "duration": 4.5,
        "segments": [
            {
                "start": 0.0,
                "end": 4.5,
                "text": "Hello, this is a test.",
            }
        ],
    }

    def fake_transcribe_audio(audio_path):
        return fake_result

    monkeypatch.setattr(
        "speech.api.main.transcribe_audio",
        fake_transcribe_audio,
    )
    monkeypatch.setattr(
        "speech.api.main.validate_audio_file",
        lambda audio_path: None,
    )

    response = client.post(
        "/api/v1/transcriptions",
        files={
            "file": (
                "sample.m4a",
                b"fake audio content",
                "audio/mp4",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["text"] == "Hello, this is a test."
    assert data["language"] == "en"
    assert data["duration"] == 4.5
    assert len(data["segments"]) == 1
