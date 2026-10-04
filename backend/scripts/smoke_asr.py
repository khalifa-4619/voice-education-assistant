"""Milestone 1 smoke test: audio -> N-ATLaS ASR -> transcript.

Run from the backend directory:
    python -m scripts.smoke_asr audio_samples/test_en_ng.wav

The -m form is required. Running `python scripts/smoke_asr.py` puts
scripts/ on sys.path, not the backend root, and `app` would not import.

Note on latency: each invocation is a fresh process and pays a cold-start
cost (~65 s on an i5-5300U). Warm in-process inference is measured at
roughly 11.5 s for a 16 s clip. The eventual FastAPI service will load
the model once and keep it resident, so per-request latency will be close
to the warm figure, not the cold figure.

This exercises the LocalNATLASASR adapter against one audio file and prints
the transcript and timing. It does not test the hosted adapter, which is a
documented stub.

The OMP_NUM_THREADS / MKL_NUM_THREADS environment variables are set here
because they must be in place before torch is imported anywhere in the
process. The adapter imports torch lazily, so setting them at the top of
this script is sufficient.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

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
    print("loading model (first run downloads weights, later runs use cache)...")

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
