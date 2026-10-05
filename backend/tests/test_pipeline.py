"""Tests for the voice education pipeline orchestrator.

These use a fake ASR and a fake LLM so that the pipeline logic can be
tested without downloading models, without a GPU, and without network
access. The real adapters are exercised by their own smoke tests; this
file is only about the orchestration.
"""

from pathlib import Path

import pytest

from app.asr.base import NATLASASR
from app.llm.base import EducationalLLM
from app.pipeline import PipelineResult, VoiceEducationPipeline


class FakeASR(NATLASASR):
    """Records calls and returns a fixed transcript."""

    def __init__(self, transcript: str = "what is photosynthesis") -> None:
        self._transcript = transcript
        self.calls: list[Path] = []

    def transcribe(self, audio_path: Path) -> str:
        self.calls.append(audio_path)
        return self._transcript


class FakeLLM(EducationalLLM):
    """Records calls and returns a fixed answer."""

    def __init__(self, answer: str = "Plants make food from sunlight.") -> None:
        self._answer = answer
        self.calls: list[str] = []

    def answer(self, question: str) -> str:
        self.calls.append(question)
        return self._answer


def _make_audio(tmp_path: Path) -> Path:
    """Create a file that satisfies the pipeline's existence check.

    The pipeline does not read the file -- it delegates to the ASR adapter.
    The fakes do not read it either. So any file will do.
    """
    audio = tmp_path / "fake.wav"
    audio.write_bytes(b"fake audio bytes")
    return audio


def test_pipeline_chains_asr_then_llm(tmp_path: Path) -> None:
    audio = _make_audio(tmp_path)
    asr = FakeASR(transcript="what is photosynthesis")
    llm = FakeLLM(answer="Plants make food from sunlight.")
    pipeline = VoiceEducationPipeline(asr=asr, llm=llm)

    result = pipeline.ask(audio)

    assert isinstance(result, PipelineResult)
    assert result.transcript == "what is photosynthesis"
    assert result.answer == "Plants make food from sunlight."
    assert asr.calls == [audio]
    assert llm.calls == ["what is photosynthesis"]


def test_pipeline_raises_on_missing_audio(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.wav"
    pipeline = VoiceEducationPipeline(asr=FakeASR(), llm=FakeLLM())

    with pytest.raises(FileNotFoundError):
        pipeline.ask(missing)


def test_pipeline_propagates_asr_errors(tmp_path: Path) -> None:
    audio = _make_audio(tmp_path)

    class BrokenASR(NATLASASR):
        def transcribe(self, audio_path: Path) -> str:
            raise RuntimeError("ASR exploded")

    pipeline = VoiceEducationPipeline(asr=BrokenASR(), llm=FakeLLM())

    with pytest.raises(RuntimeError, match="ASR exploded"):
        pipeline.ask(audio)


def test_pipeline_propagates_llm_errors(tmp_path: Path) -> None:
    audio = _make_audio(tmp_path)

    class BrokenLLM(EducationalLLM):
        def answer(self, question: str) -> str:
            raise RuntimeError("LLM exploded")

    pipeline = VoiceEducationPipeline(asr=FakeASR(), llm=BrokenLLM())

    with pytest.raises(RuntimeError, match="LLM exploded"):
        pipeline.ask(audio)


def test_pipeline_records_timings(tmp_path: Path) -> None:
    audio = _make_audio(tmp_path)

    result = VoiceEducationPipeline(asr=FakeASR(), llm=FakeLLM()).ask(audio)

    assert result.asr_seconds >= 0
    assert result.llm_seconds >= 0
    # total includes the small overhead between stages, so it is >= the sum.
    assert result.total_seconds >= result.asr_seconds + result.llm_seconds
