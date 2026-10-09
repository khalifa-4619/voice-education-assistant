"""Local N-ATLaS ASR adapter using the official NCAIR1 Hugging Face model.

This adapter runs inference locally using the transformers Whisper classes
directly (WhisperProcessor + WhisperForConditionalGeneration), following the
"Advanced Usage" example published on the model card.

We deliberately do NOT use the transformers pipeline() here. On this project's
hardware (2-core / 4-thread CPU), pipeline() was measured at ~100x slower than
the direct model call for identical output. The direct call is the model card's
documented path; the pipeline was our earlier choice, and measurement led us
to change it.

Audio format handling:
  soundfile (used by librosa) cannot decode some browser-produced formats,
  notably WebM/Opus from Chrome and Edge. Newer versions of librosa no
  longer fall back to ffmpeg automatically. So this adapter pre-converts
  any file that soundfile rejects into a temporary 16 kHz mono WAV using
  the system ffmpeg binary, then hands that WAV to librosa. Files that
  soundfile can already read bypass the conversion entirely.

Model:   NCAIR1/NigerianAccentedEnglish (and future NCAIR1/* ASR models)
Input:   16 kHz mono audio (any format ffmpeg can decode)
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.asr.base import NATLASASR


class LocalNATLASASR(NATLASASR):
    """Local N-ATLaS ASR using the official NCAIR1 Hugging Face model.

    The processor and model are lazy-loaded on first use so that importing
    this module does not pull ~1 GB of weights into memory.
    """

    def __init__(
        self,
        model_id: str = "NCAIR1/NigerianAccentedEnglish",
        language: str = "en",
        task: str = "transcribe",
        max_new_tokens: int = 225,
        num_threads: int = 2,
    ) -> None:
        self._model_id = model_id
        self._language = language
        self._task = task
        self._max_new_tokens = max_new_tokens
        self._num_threads = num_threads
        self._processor = None
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return

        import torch
        from transformers import (
            WhisperForConditionalGeneration,
            WhisperProcessor,
        )

        # Cap at physical-core count. This CPU has 2 cores / 4 threads;
        # PyTorch defaults to the logical count and oversubscribes.
        torch.set_num_threads(self._num_threads)

        self._processor = WhisperProcessor.from_pretrained(self._model_id)
        self._model = WhisperForConditionalGeneration.from_pretrained(self._model_id)
        self._model.eval()

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load()

        import librosa
        import torch

        readable_path = _ensure_librosa_readable(audio_path)
        try:
            audio, sr = librosa.load(str(readable_path), sr=16000)
        finally:
            if readable_path != audio_path:
                readable_path.unlink(missing_ok=True)

        inputs = self._processor(audio, sampling_rate=sr, return_tensors="pt")

        with torch.no_grad():
            generated = self._model.generate(
                inputs.input_features,
                language=self._language,
                task=self._task,
                max_new_tokens=self._max_new_tokens,
            )

        text = self._processor.batch_decode(generated, skip_special_tokens=True)[0]
        return text


def _ensure_librosa_readable(audio_path: Path) -> Path:
    """Return a path that librosa can load.

    First tries soundfile directly. If the format is unsupported (e.g. WebM
    from a browser), converts to a temporary 16 kHz mono WAV via ffmpeg and
    returns that path. The caller is responsible for cleaning up the
    returned path if it differs from the input.

    Raises RuntimeError if ffmpeg is not available and conversion is needed.
    """
    import soundfile as sf

    try:
        # Probe: does soundfile recognise this file?
        with sf.SoundFile(str(audio_path)):
            return audio_path
    except (sf.LibsndfileError, RuntimeError):
        pass  # Fall through to ffmpeg conversion.

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            f"Audio file {audio_path.name!r} is in a format soundfile cannot "
            "read, and ffmpeg was not found on PATH. Install ffmpeg or "
            "convert the file to WAV before submitting."
        )

    fd, tmp_name = tempfile.mkstemp(suffix=".wav")
    # Close the file descriptor; ffmpeg will open the file by path.
    import os
    os.close(fd)

    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",            # overwrite the output file
                "-i", str(audio_path),
                "-ar", "16000",  # resample to 16 kHz
                "-ac", "1",      # downmix to mono
                "-f", "wav",
                tmp_name,
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        Path(tmp_name).unlink(missing_ok=True)
        raise RuntimeError(
            f"ffmpeg failed to convert {audio_path.name!r}: "
            f"{exc.stderr.decode(errors='replace')[:300]}"
        ) from exc

    return Path(tmp_name)
