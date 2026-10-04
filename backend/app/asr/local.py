"""Local N-ATLaS ASR adapter using the official NCAIR1 Hugging Face model.

This adapter runs inference locally using the transformers Whisper classes
directly (WhisperProcessor + WhisperForConditionalGeneration), following the
"Advanced Usage" example published on the model card.

We deliberately do NOT use the transformers pipeline() here. On this project's
hardware (2-core / 4-thread CPU), pipeline() was measured at ~100x slower than
the direct model call for identical output. The direct call is the model card's
documented path; the pipeline was our earlier choice, and measurement led us
to change it.

Model:   NCAIR1/NigerianAccentedEnglish (and future NCAIR1/* ASR models)
Input:   16 kHz mono audio
"""

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

        audio, sr = librosa.load(str(audio_path), sr=16000)
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
