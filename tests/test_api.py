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


def test_create_async_job(monkeypatch):
    monkeypatch.setattr(
        "speech.api.main.validate_audio_file",
        lambda audio_path: None,
    )

    def fake_create_transcription_job(
        audio_path,
        original_filename,
    ):
        return {
            "job_id": "test-job-123",
            "status": "queued",
        }

    monkeypatch.setattr(
        "speech.api.main.create_transcription_job",
        fake_create_transcription_job,
    )

    response = client.post(
        "/api/v1/jobs",
        files={
            "file": (
                "sample.m4a",
                b"fake audio content",
                "audio/mp4",
            )
        },
    )

    assert response.status_code == 202

    assert response.json() == {
        "job_id": "test-job-123",
        "status": "queued",
    }


def test_get_job_status_queued(monkeypatch):
    monkeypatch.setattr(
        "speech.api.main.get_transcription_result",
        lambda job_id: None,
    )

    response = client.get("/api/v1/jobs/test-job-123")

    assert response.status_code == 200

    assert response.json() == {
        "job_id": "test-job-123",
        "status": "queued",
        "result": None,
    }


def test_get_job_status_completed(monkeypatch):
    result = {
        "text": "Hello from Whisper.",
        "language": "en",
        "language_probability": 1.0,
        "duration": 2.0,
        "segments": [],
    }

    monkeypatch.setattr(
        "speech.api.main.get_transcription_result",
        lambda job_id: result,
    )

    response = client.get("/api/v1/jobs/test-job-123")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "test-job-123"
    assert data["status"] == "completed"
    assert data["result"]["text"] == "Hello from Whisper."
