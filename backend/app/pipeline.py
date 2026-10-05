"""Voice education pipeline: audio -> ASR -> question -> LLM -> answer.

This module defines the orchestrator that chains the ASR adapter and the
EducationalLLM adapter into a single, testable unit. It is deliberately
small: its job is to sequence the two stages, time them, and return a
structured result. It does not know or care which concrete ASR or LLM
implementation it is given -- that is the point of the adapter interfaces.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.asr.base import NATLASASR
from app.llm.base import EducationalLLM


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of one full voice-question -> spoken-answer cycle.

    Frozen because the pipeline should never mutate a result after it is
    returned. If a caller wants a modified copy, they use dataclasses.replace.
    """

    audio_path: Path
    transcript: str
    answer: str
    asr_seconds: float
    llm_seconds: float
    total_seconds: float
    started_at: datetime


class VoiceEducationPipeline:
    """Sequences ASR and LLM into a single question-answering flow.

    Construction takes the two adapters as arguments (dependency injection).
    This lets the caller swap the local ASR for a hosted one, or the stub LLM
    for a real one, without touching this class. It also makes the pipeline
    trivially testable: pass a real ASR and a fake LLM, or two fakes.
    """

    def __init__(self, asr: NATLASASR, llm: EducationalLLM) -> None:
        self._asr = asr
        self._llm = llm

    def ask(self, audio_path: Path) -> PipelineResult:
        """Run one full cycle: audio file in, answer text out.

        Raises FileNotFoundError if audio_path does not exist.
        Propagates any exception raised by the ASR or LLM adapter.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        started_at = datetime.now(timezone.utc)
        total_t0 = time.perf_counter()

        asr_t0 = time.perf_counter()
        transcript = self._asr.transcribe(audio_path)
        asr_seconds = time.perf_counter() - asr_t0

        llm_t0 = time.perf_counter()
        answer = self._llm.answer(transcript)
        llm_seconds = time.perf_counter() - llm_t0

        total_seconds = time.perf_counter() - total_t0

        return PipelineResult(
            audio_path=audio_path,
            transcript=transcript,
            answer=answer,
            asr_seconds=asr_seconds,
            llm_seconds=llm_seconds,
            total_seconds=total_seconds,
            started_at=started_at,
        )
