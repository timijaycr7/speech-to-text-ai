from typing import Any

from pydantic import BaseModel


class Segment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    duration: float
    segments: list[Segment]


class JobResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict[str, Any] | None = None
