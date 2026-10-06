"""Deterministic fake N-ATLaS ASR adapter for tests and local development.

This is NOT N-ATLaS ASR. It performs no speech recognition. It exists so the
application architecture can be exercised end-to-end without loading a real
ASR model, without a GPU, and without network access.

Use it only when ASR_PROVIDER=fake is set. Do not represent its output as
N-ATLaS in any user-facing context.
"""

from pathlib import Path

from app.asr.base import NATLASASR


class FakeNATLASASR(NATLASASR):
    """Returns a fixed transcript regardless of input.

    The default transcript is a short educational question so that the fake
    LLM downstream has something plausible to "answer".
    """

    def __init__(self, transcript: str = "What is photosynthesis?") -> None:
        self._transcript = transcript
        self.calls: list[Path] = []

    def transcribe(self, audio_path: Path) -> str:
        self.calls.append(audio_path)
        return self._transcript
