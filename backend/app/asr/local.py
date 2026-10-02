"""Local N-ATLaS ASR adapter using the official NCAIR1 Hugging Face model.

This adapter runs inference locally via the transformers pipeline. It uses
the official NCAIR1 model as documented on Hugging Face. It is NOT the same
as the challenge's hosted service, and this distinction is documented here
and in the project README.

Model: NCAIR1/NigerianAccentedEnglish (or NCAIR1/Hausa-ASR)
Architecture: Whisper Small (244M parameters)
Input: 16 kHz mono audio
"""

from pathlib import Path

from app.asr.base import NATLASASR


class LocalNATLASASR(NATLASASR):
    """Local N-ATLaS ASR using the official NCAIR1 Hugging Face model.

    The transformers pipeline is lazy-loaded on first use so that merely
    importing this module does not download ~1 GB of weights.
    """

    def __init__(self, model_id: str = "NCAIR1/NigerianAccentedEnglish") -> None:
        self._model_id = model_id
        self._pipeline = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        from transformers import pipeline

        self._pipeline = pipeline(
            "automatic-speech-recognition",
            model=self._model_id,
        )

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load()

        # librosa handles resampling to 16 kHz and loading common formats.
        import librosa

        audio, _ = librosa.load(str(audio_path), sr=16000)
        result = self._pipeline(audio)
        return result["text"]