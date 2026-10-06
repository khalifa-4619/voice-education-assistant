"""Tests for the FastAPI HTTP layer's baseline behavior.

These use fastapi.testclient.TestClient, which runs the app in-process and
speaks real HTTP through ASGI without binding a port. The lifespan runs when
the client is used as a context manager, so build_pipeline() is exercised
end-to-end against the fake providers.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok(monkeypatch):
    monkeypatch.delenv("ASR_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["providers"] == {"asr": "fake", "llm": "fake"}


def test_health_reports_selected_providers(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["providers"]["asr"] == "fake"
    assert body["providers"]["llm"] == "fake"


def test_cors_allows_dev_origin(monkeypatch):
    # CORS preflight: browsers send OPTIONS before a cross-origin POST.
    with TestClient(app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_rejects_unknown_origin(monkeypatch):
    with TestClient(app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    # Starlette's CORSMiddleware returns 400 for disallowed preflight origins.
    assert response.status_code == 400
