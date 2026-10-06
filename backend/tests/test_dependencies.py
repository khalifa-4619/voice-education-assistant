"""Tests for the composition root.

These prove that environment variables select the intended adapter, and that
the default configuration produces a working pipeline. No model, no GPU, no
network. Pure configuration wiring.
"""

from pathlib import Path

import pytest

from app.dependencies import build_pipeline


def _fake_audio(tmp_path: Path) -> Path:
    audio = tmp_path / "fake.wav"
    audio.write_bytes(b"fake audio bytes")
    return audio


def test_defaults_to_fake_providers(monkeypatch, tmp_path):
    monkeypatch.delenv("ASR_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    pipeline = build_pipeline()
    result = pipeline.ask(_fake_audio(tmp_path))

    # The fake ASR's default transcript
    assert result.transcript == "What is photosynthesis?"
    # The fake LLM's default answer
    assert "photosynthesis" in result.answer.lower()


def test_explicit_fake_providers(monkeypatch, tmp_path):
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    pipeline = build_pipeline()
    result = pipeline.ask(_fake_audio(tmp_path))

    assert result.transcript
    assert result.answer


def test_unknown_asr_provider_raises(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "nonsense")

    with pytest.raises(ValueError, match="Unknown ASR_PROVIDER"):
        build_pipeline()


def test_unknown_llm_provider_raises(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "nonsense")

    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        build_pipeline()


def test_hosted_llm_provider_is_documented_stub(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "hosted")

    with pytest.raises(NotImplementedError, match="HostedNATLASLLM is a documented stub"):
        build_pipeline()


def test_local_llm_provider_is_documented_hardware_block(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "local")

    with pytest.raises(NotImplementedError, match="6-8 GB free RAM"):
        build_pipeline()
