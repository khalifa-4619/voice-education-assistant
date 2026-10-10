"""Append-only JSON Lines log of student interactions.

This module is deliberately simple: one file, one line per record, append
only. The purpose is to produce the documented evidence required by the
NAIC 2026 challenge for Problem Statement 2 (50+ real-user interactions).

The file lives at docs/validation/interactions.jsonl by default. That path
is relative to the repository root; the module resolves it robustly from
its own location so that the code works regardless of the current working
directory the server was started from.

Limitations (documented, not bugs):
  - Not concurrency-safe across processes. Fine for a single-laptop
    prototype. Would need a lock or a proper sink in production.
  - No rotation, no retention policy. Validation records are expected
    to be small.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# backend/app/validation/log.py -> backend/app/validation -> backend/app
# -> backend -> repo_root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_LOG_PATH = _REPO_ROOT / "docs" / "validation" / "interactions.jsonl"


def _log_path() -> Path:
    """Resolve the log path and ensure the parent directory exists."""
    _DEFAULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_LOG_PATH


def append_interaction(record: dict[str, Any]) -> None:
    """Append one interaction record as a single line of JSON.

    The record is augmented with a UTC timestamp if it does not already
    have one under the key "recorded_at".
    """
    record = dict(record)  # do not mutate the caller's dict
    record.setdefault(
        "recorded_at", datetime.now(timezone.utc).isoformat()
    )
    line = json.dumps(record, ensure_ascii=False)
    with _log_path().open("a", encoding="utf-8") as f:
        f.write(line + "\n")
