"""Tests for /api/v1/ask's interaction_id and /api/v1/feedback.

The validation log file is patched to a tmp file so tests never touch the
real docs/validation/interactions.jsonl.
"""

import json
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    with TestClient(app) as c:
        yield c


def _fake_audio() -> BytesIO:
    return BytesIO(b"RIFF....WAVEfmt  fake")


@pytest.fixture
def validation_log(tmp_path, monkeypatch):
    """Redirect append_interaction to a tmp file for each test."""
    log = tmp_path / "interactions.jsonl"
    from app.api import routes

    def _fake_append(record):
        from datetime import datetime, timezone

        record = dict(record)
        record.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    monkeypatch.setattr(routes, "append_interaction", _fake_append)
    return log


def _read_records(log):
    return [json.loads(line) for line in log.read_text().splitlines() if line]


def test_ask_returns_interaction_id(client, validation_log):
    response = client.post(
        "/api/v1/ask",
        files={"audio": ("q.wav", _fake_audio(), "audio/wav")},
    )
    assert response.status_code == 200
    body = response.json()
    assert "interaction_id" in body
    assert len(body["interaction_id"]) >= 32  # uuid4 shape


def test_ask_appends_an_ask_record(client, validation_log):
    response = client.post(
        "/api/v1/ask",
        files={"audio": ("q.wav", _fake_audio(), "audio/wav")},
    )
    interaction_id = response.json()["interaction_id"]

    records = _read_records(validation_log)
    assert len(records) == 1
    rec = records[0]
    assert rec["kind"] == "ask"
    assert rec["interaction_id"] == interaction_id
    assert rec["transcript"]
    assert rec["answer"]


def test_feedback_is_appended_with_same_id(client, validation_log):
    ask = client.post(
        "/api/v1/ask",
        files={"audio": ("q.wav", _fake_audio(), "audio/wav")},
    ).json()

    response = client.post(
        "/api/v1/feedback",
        json={
            "interaction_id": ask["interaction_id"],
            "useful": True,
            "language": "en",
            "subject": "science",
            "notes": "Clear explanation.",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "recorded": True,
        "interaction_id": ask["interaction_id"],
    }

    records = _read_records(validation_log)
    assert len(records) == 2
    feedback_rec = records[1]
    assert feedback_rec["kind"] == "feedback"
    assert feedback_rec["interaction_id"] == ask["interaction_id"]
    assert feedback_rec["useful"] is True
    assert feedback_rec["language"] == "en"
    assert feedback_rec["subject"] == "science"
    assert feedback_rec["notes"] == "Clear explanation."


def test_feedback_requires_interaction_id(client):
    response = client.post(
        "/api/v1/feedback",
        json={"useful": True},
    )
    assert response.status_code == 422  # FastAPI validation


def test_feedback_notes_length_is_capped(client):
    response = client.post(
        "/api/v1/feedback",
        json={
            "interaction_id": "x" * 36,
            "useful": False,
            "notes": "y" * 3000,  # over the 2000 limit
        },
    )
    assert response.status_code == 422
