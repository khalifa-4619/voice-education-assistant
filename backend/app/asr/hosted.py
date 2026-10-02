"""Hosted N-ATLaS ASR adapter (placeholder).

This adapter will connect to the official NCAIR/N-ATLaS hosted ASR endpoint
once the NAIC 2026 challenge provides API credentials and endpoint schema.

It is intentionally non-functional right now. Do not delete it: it documents
the intended integration point and prevents accidental assumption that
hosted access is available.
"""

from pathlib import Path

from app.asr.base import NATLASASR


class HostedNATLASASR(NATLASASR):
    """Placeholder for the official hosted N-ATLaS ASR service.

    Status: BLOCKED — awaiting challenge API credentials and endpoint schema.
    """

    def __init__(self, endpoint: str, api_key: str) -> None:
        self._endpoint = endpoint
        self._api_key = api_key

    def transcribe(self, audio_path: Path) -> str:
        raise NotImplementedError(
            "Hosted N-ATLaS ASR is not yet available. "
            "The NAIC 2026 challenge has not published the endpoint schema, "
            "authentication mechanism, or request/response format. "
            "Use LocalNATLASASR for Milestone 1 PoC."
        )