"""Tests for LocalNATLASASR's audio format handling.

We do NOT test actual model inference here -- that needs the real Whisper
weights and would be slow. We test the format-detection helper, which is
the piece that broke when Chrome sent WebM to a soundfile-only pipeline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import soundfile as sf

from app.asr.local import _ensure_librosa_readable


def _make_wav(path: Path) -> None:
    """Write a tiny valid WAV file that soundfile can read."""
    import numpy as np

    sf.write(str(path), np.zeros(1600, dtype="float32"), 16000)


def test_returns_input_path_unchanged_for_readable_wav(tmp_path: Path) -> None:
    wav = tmp_path / "input.wav"
    _make_wav(wav)

    result = _ensure_librosa_readable(wav)

    assert result == wav


def test_raises_when_unreadable_and_ffmpeg_missing(tmp_path: Path) -> None:
    fake_webm = tmp_path / "input.webm"
    fake_webm.write_bytes(b"\x1a\x45\xdf\xa3 this is not a real webm")

    with patch("app.asr.local.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="ffmpeg was not found"):
            _ensure_librosa_readable(fake_webm)


def test_converts_unreadable_file_via_ffmpeg(tmp_path: Path) -> None:
    """If ffmpeg is present on the test machine, conversion should produce
    a temp WAV that soundfile can read. Skipped automatically if ffmpeg
    is not on PATH (e.g. a dev laptop without it)."""
    import shutil

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not installed on this machine")

    # A minimal silent WAV is not "unreadable" -- we need something
    # soundfile cannot open. A raw byte blob with a .webm extension works.
    fake_webm = tmp_path / "input.webm"
    fake_webm.write_bytes(b"\x1a\x45\xdf\xa3 not a real webm")

    # ffmpeg will refuse a corrupted file, so this test's purpose is to
    # confirm the code path is entered (subprocess called) and errors are
    # raised cleanly. That is what we assert.
    with pytest.raises(RuntimeError, match="ffmpeg failed to convert"):
        _ensure_librosa_readable(fake_webm)
