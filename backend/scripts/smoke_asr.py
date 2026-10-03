"""Milestone 1 smoke test: audio -> N-ATLaS ASR -> transcript.

Run from the backend directory:
    python scripts/smoke_asr.py audio_samples/test_en_ng.wav

This is intentionally minimal. It exercises the LocalNATLASASR adapter
against one audio file and prints the transcript and timing. It does not
test the hosted adapter, which is a documented stub.
"""

import sys
import time
from pathlib import Path

from app.asr import LocalNATLASASR


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/smoke_asr.py <audio_path>")
        return 2

    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"error: file not found: {audio_path}")
        return 1

    print("model: NCAIR1/NigerianAccentedEnglish")
    print(f"audio: {audio_path}")
    print("loading model (first run downloads ~1 GB, later runs use cache)...")

    asr = LocalNATLASASR()

    t0 = time.perf_counter()
    transcript = asr.transcribe(audio_path)
    elapsed = time.perf_counter() - t0

    print("---")
    print(f"transcript: {transcript!r}")
    print(f"elapsed_s: {elapsed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
