"""Environment-based configuration for the backend.

Only settings that genuinely vary between environments live here. The
defaults are chosen so the app runs with no configuration at all: fake
providers, a 10 MB upload limit, common audio extensions. Every value can
be overridden by an environment variable.

Configuration is read on each call to get_settings() rather than cached at
import time. That keeps tests simple (monkeypatch env, call get_settings)
and avoids the common bug where config is captured before a test can
override it.
"""

import os
from dataclasses import dataclass


_DEFAULT_MAX_MB = 10
_DEFAULT_ALLOWED = "wav,mp3,m4a,webm,ogg,flac"


@dataclass(frozen=True)
class Settings:
    max_audio_bytes: int
    allowed_extensions: frozenset[str]


def _parse_extensions(raw: str) -> frozenset[str]:
    """Turn 'wav, mp3,M4A' into frozenset({'wav', 'mp3', 'm4a'})."""
    return frozenset(
        ext.strip().lower().lstrip(".")
        for ext in raw.split(",")
        if ext.strip()
    )


def get_settings() -> Settings:
    max_mb_raw = os.environ.get("MAX_AUDIO_SIZE_MB", str(_DEFAULT_MAX_MB))
    try:
        max_mb = int(max_mb_raw)
        if max_mb <= 0:
            raise ValueError("must be positive")
    except ValueError as exc:
        raise ValueError(
            f"MAX_AUDIO_SIZE_MB must be a positive integer, got {max_mb_raw!r}"
        ) from exc

    allowed_raw = os.environ.get("ALLOWED_AUDIO_TYPES", _DEFAULT_ALLOWED)
    allowed = _parse_extensions(allowed_raw)
    if not allowed:
        raise ValueError("ALLOWED_AUDIO_TYPES must list at least one extension")

    return Settings(
        max_audio_bytes=max_mb * 1024 * 1024,
        allowed_extensions=allowed,
    )
