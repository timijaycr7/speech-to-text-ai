import json
from types import SimpleNamespace

from speech.worker.main import process_message, process_next_message


def test_process_message(monkeypatch):
    uploaded_result = {}

    monkeypatch.setattr(
        "speech.worker.main.get_settings",
        lambda: SimpleNamespace(
            s3_bucket="test-bucket",
        ),
    )

    def fake_download_audio(
        bucket,
        object_key,
        destination,
    ):
        assert bucket == "test-bucket"
        assert object_key == "uploads/test-job/input.m4a"

        destination.write_bytes(b"fake audio")

    monkeypatch.setattr(
        "speech.worker.main.download_audio",
        fake_download_audio,
    )

    def fake_transcribe_audio(audio_path):
        assert audio_path.exists()

        return {
            "text": "Hello from the worker.",
            "language": "en",
            "language_probability": 1.0,
            "duration": 2.0,
            "segments": [],
        }

    monkeypatch.setattr(
        "speech.worker.main.transcribe_audio",
        fake_transcribe_audio,
    )

    def fake_upload_transcription_result(
        job_id,
        result,
    ):
        uploaded_result["job_id"] = job_id
        uploaded_result["result"] = result

        return f"s3://test-bucket/results/{job_id}.json"

    monkeypatch.setattr(
        "speech.worker.main.upload_transcription_result",
        fake_upload_transcription_result,
    )

    message = {
        "job_id": "test-job",
        "s3_bucket": "test-bucket",
        "s3_key": "uploads/test-job/input.m4a",
    }

    process_message(json.dumps(message))

    assert uploaded_result["job_id"] == "test-job"
    assert uploaded_result["result"]["text"] == "Hello from the worker."
    assert uploaded_result["result"]["language"] == "en"


class FakeSQS:
    def __init__(self, body: str):
        self.body = body
        self.deleted_messages = []

    def receive_message(
        self,
        QueueUrl,
        MaxNumberOfMessages,
        WaitTimeSeconds,
    ):
        return {
            "Messages": [
                {
                    "Body": self.body,
                    "ReceiptHandle": "receipt-123",
                }
            ]
        }

    def delete_message(
        self,
        QueueUrl,
        ReceiptHandle,
    ):
        self.deleted_messages.append(
            {
                "QueueUrl": QueueUrl,
                "ReceiptHandle": ReceiptHandle,
            }
        )


def test_successful_message_is_deleted(monkeypatch):
    sqs = FakeSQS('{"job_id": "test-job"}')

    monkeypatch.setattr(
        "speech.worker.main.process_message",
        lambda body: None,
    )

    processed = process_next_message(
        sqs=sqs,
        queue_url="https://example.com/test-queue",
    )

    assert processed is True
    assert len(sqs.deleted_messages) == 1
    assert sqs.deleted_messages[0]["ReceiptHandle"] == "receipt-123"


def test_failed_message_is_not_deleted(monkeypatch):
    sqs = FakeSQS('{"job_id": "test-job"}')

    def fail_processing(body):
        raise RuntimeError("Transcription failed")

    monkeypatch.setattr(
        "speech.worker.main.process_message",
        fail_processing,
    )

    processed = process_next_message(
        sqs=sqs,
        queue_url="https://example.com/test-queue",
    )

    assert processed is True
    assert sqs.deleted_messages == []
