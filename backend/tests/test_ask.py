"""Tests for POST /api/v1/ask.

Exercises the whole HTTP path: routing, form parsing, validation, the
pipeline call, response serialization. The pipeline uses fake providers,
so no model is loaded and the suite stays fast.
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _fake_audio() -> BytesIO:
    # Contents are irrelevant: FakeNATLASASR does not read them.
    return BytesIO(b"RIFF....WAVEfmt  fake-content")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.delenv("MAX_AUDIO_SIZE_MB", raising=False)
    monkeypatch.delenv("ALLOWED_AUDIO_TYPES", raising=False)
    with TestClient(app) as c:
        yield c


def test_ask_happy_path(client):
    response = client.post(
        "/api/v1/ask",
        files={"audio": ("question.wav", _fake_audio(), "audio/wav")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["transcript"]
    assert body["answer"]
    assert body["asr_seconds"] >= 0
    assert body["llm_seconds"] >= 0
    assert body["total_seconds"] >= 0
    assert body["started_at"]


def test_ask_rejects_unsupported_extension(client):
    response = client.post(
        "/api/v1/ask",
        files={"audio": ("notes.txt", _fake_audio(), "text/plain")},
    )
    assert response.status_code == 415
    assert "Unsupported audio extension" in response.json()["detail"]


def test_ask_rejects_missing_extension(client):
    response = client.post(
        "/api/v1/ask",
        files={"audio": ("noextension", _fake_audio(), "application/octet-stream")},
    )
    assert response.status_code == 415


def test_ask_rejects_oversized_upload(client, monkeypatch):
    monkeypatch.setenv("MAX_AUDIO_SIZE_MB", "1")
    payload = BytesIO(b"x" * (2 * 1024 * 1024))
    response = client.post(
        "/api/v1/ask",
        files={"audio": ("big.wav", payload, "audio/wav")},
    )
    assert response.status_code == 413
    assert "exceeds maximum size" in response.json()["detail"]


def test_ask_missing_audio_field_returns_422(client):
    response = client.post("/api/v1/ask")
    assert response.status_code == 422


def test_ask_returns_503_when_pipeline_raises_not_implemented(client):
    class ExplodingASR:
        def transcribe(self, audio_path):
            raise NotImplementedError("stub not configured")

    from app.asr.fake import FakeNATLASASR
    from app.pipeline import VoiceEducationPipeline

    class NoopLLM:
        def answer(self, question):
            return "never reached"

    # Replace the pipeline for the duration of this test.
    original = client.app.state.pipeline
    client.app.state.pipeline = VoiceEducationPipeline(
        asr=ExplodingASR(), llm=NoopLLM()
    )
    try:
        response = client.post(
            "/api/v1/ask",
            files={"audio": ("q.wav", _fake_audio(), "audio/wav")},
        )
    finally:
        client.app.state.pipeline = original

    assert response.status_code == 503
    assert "stub not configured" in response.json()["detail"]


def test_ask_cleans_up_temp_file(client, tmp_path, monkeypatch):
    """After a successful request, no leftover audio file should remain
    in the system temp directory that matches our suffix pattern for this
    call. This is a soft check: we look for files created during the test
    window and assert none of them persist."""
    import tempfile
    from pathlib import Path

    before = set(Path(tempfile.gettempdir()).glob("*.wav"))

    response = client.post(
        "/api/v1/ask",
        files={"audio": ("cleanup.wav", _fake_audio(), "audio/wav")},
    )
    assert response.status_code == 200

    after = set(Path(tempfile.gettempdir()).glob("*.wav"))
    new_leftovers = after - before
    assert new_leftovers == set(), f"temp files not cleaned: {new_leftovers}"
