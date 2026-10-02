"""Abstract interface for N-ATLaS ASR.

The rest of the application depends only on this interface, never on a
concrete implementation. This lets us swap local inference for the official
hosted endpoint without touching any caller.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class NATLASASR(ABC):
    """N-ATLaS Automatic Speech Recognition interface.

    Implementations must accept a path to an audio file and return the
    transcribed text. The interface is intentionally minimal: no streaming,
    no batching, no language selection parameter yet. We add those only when
    a real requirement demands them.
    """

    @abstractmethod
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to a 16 kHz mono audio file.

        Returns:
            The transcribed text as a single string.

        Raises:
            FileNotFoundError: If audio_path does not exist.
            RuntimeError: If the underlying ASR engine fails.
        """
        raise NotImplementedError