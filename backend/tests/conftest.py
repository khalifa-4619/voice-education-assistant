"""Global pytest configuration for the backend test suite.

Every test that exercises the HTTP route will trigger interaction logging
via app.validation.log.append_interaction. That call writes to the real
docs/validation/interactions.jsonl, which we do not want during tests.
This conftest redirects every append_interaction call to a per-test tmp
file, so the real log only ever contains real student interactions.
"""

import json
from datetime import datetime, timezone

import pytest


@pytest.fixture(autouse=True)
def _isolate_validation_log(tmp_path, monkeypatch):
    """Redirect all validation log writes to a tmp file per test."""
    log_file = tmp_path / "interactions.jsonl"

    def _fake_append(record):
        record = dict(record)
        record.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Patch at both import sites so it works regardless of which module the
    # test path goes through.
    import app.api.routes as routes_module
    import app.validation.log as log_module

    monkeypatch.setattr(routes_module, "append_interaction", _fake_append)
    monkeypatch.setattr(log_module, "append_interaction", _fake_append)
    yield log_file
