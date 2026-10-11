"""Extract summary statistics from docs/validation/interactions.jsonl.

Writes docs/validation/SUMMARY.md with the results filled in.
Run from the repository root:
    python3 docs/scripts/validation_stats.py
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "docs" / "validation" / "interactions.jsonl"
OUT = ROOT / "docs" / "validation" / "SUMMARY.md"

asks = []
feedbacks = []
with LOG.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("kind") == "ask":
            asks.append(rec)
        elif rec.get("kind") == "feedback":
            feedbacks.append(rec)

# Feedback is joined to asks by interaction_id.
fb_by_id = {fb["interaction_id"]: fb for fb in feedbacks}
useful_true = sum(1 for fb in feedbacks if fb.get("useful") is True)
useful_false = sum(1 for fb in feedbacks if fb.get("useful") is False)
no_feedback = len(asks) - len({fb["interaction_id"] for fb in feedbacks})

# Timings
tot_asr = sum(a.get("asr_seconds", 0.0) for a in asks) / len(asks) if asks else 0
tot_llm = sum(a.get("llm_seconds", 0.0) for a in asks) / len(asks) if asks else 0
tot_tot = sum(a.get("total_seconds", 0.0) for a in asks) / len(asks) if asks else 0

min_tot = min((a.get("total_seconds", 0.0) for a in asks), default=0)
max_tot = max((a.get("total_seconds", 0.0) for a in asks), default=0)

# Language and subject distribution
languages = Counter(fb.get("language", "unknown") for fb in feedbacks)
subjects = Counter(fb.get("subject", "unknown") for fb in feedbacks)

# Time range
timestamps = [a["started_at"] for a in asks if "started_at" in a]
first_ts = min(timestamps) if timestamps else "unknown"
last_ts = max(timestamps) if timestamps else "unknown"

# Sample answers: pick one good, one weak
sample_good = next(
    (a for a in asks if fb_by_id.get(a["interaction_id"], {}).get("useful") is True),
    None,
)
sample_weak = next(
    (a for a in asks if fb_by_id.get(a["interaction_id"], {}).get("useful") is False),
    None,
)


def truncate(text, n=280):
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "…"


doc = f"""# Real-World Validation Summary

**Project:** Voice Education Assistant
**Challenge:** NITDA/NCAIR National AI Innovation Challenge 2026
**Problem Statement:** 2 — Voice-First Access
**Domain:** Education
**Recording period:** {first_ts} to {last_ts}

## Overview

We validated the Voice Education Assistant with {len(asks)} real interactions
recorded on a CPU-only Windows laptop. Each interaction consists of a student
speaking an educational question into the browser and receiving a spoken
answer produced by the N-ATLaS pipeline (ASR → LLM → TTS). The full pipeline
ran locally: no GPU, no cloud, no external inference API.

Of the {len(asks)} interactions, {len(feedbacks)} received explicit feedback
from the student.

## Summary statistics

| Metric | Value |
|---|---|
| Total interactions recorded | {len(asks)} |
| Interactions with feedback | {len(feedbacks)} |
| Interactions without feedback | {no_feedback} |
| Rated useful (Yes) | {useful_true} |
| Rated not useful (No) | {useful_false} |
| Useful rate (of feedback given) | {useful_true / max(1, useful_true + useful_false) * 100:.0f}% |

### Latency (per interaction)

| Stage | Average | Min total | Max total |
|---|---|---|---|
| ASR | {tot_asr:.1f} s | — | — |
| LLM | {tot_llm:.1f} s | — | — |
| Total pipeline | {tot_tot:.1f} s | {min_tot:.1f} s | {max_tot:.1f} s |

The large spread in total time is expected: the model generates answers of
variable length, and short factual answers complete much faster than long
explanatory ones.

### Languages recorded

""" + "\n".join(f"- `{lang}`: {count} interaction(s)" for lang, count in languages.most_common()) + f"""

### Subjects covered

""" + "\n".join(f"- `{subj}`: {count} interaction(s)" for subj, count in subjects.most_common()) + """

## Sample interactions

### A representative successful interaction

"""

if sample_good:
    doc += f"""- **Transcript (ASR):** {truncate(sample_good['transcript'])}
- **Answer (LLM):** {truncate(sample_good['answer'], 400)}
- **Timings:** ASR {sample_good['asr_seconds']:.1f}s · LLM {sample_good['llm_seconds']:.1f}s · Total {sample_good['total_seconds']:.1f}s
- **Student feedback:** useful

"""
else:
    doc += "_No successful-with-feedback example was found in the log._\n\n"

doc += """### A representative weaker interaction

"""

if sample_weak:
    doc += f"""- **Transcript (ASR):** {truncate(sample_weak['transcript'])}
- **Answer (LLM):** {truncate(sample_weak['answer'], 400)}
- **Timings:** ASR {sample_weak['asr_seconds']:.1f}s · LLM {sample_weak['llm_seconds']:.1f}s · Total {sample_weak['total_seconds']:.1f}s
- **Student feedback:** not useful

"""
else:
    doc += (
        "_Every interaction that received feedback was rated useful. "
        "This reflects the recording session; on a wider sample we expect "
        "a small fraction of weaker answers._\n\n"
    )

doc += """## Methodology

- **Environment:** Windows 11, Python 3.13, Chrome/Edge, FFmpeg 9.0.2,
  Ollama local server, NCAIR1/NigerianAccentedEnglish (Whisper Small),
  NCAIR1/N-ATLaS (Llama-3 8B) quantized at Q4_K_M.
- **Hardware:** 4-core / 8-thread CPU, 14 GB RAM, no GPU.
- **Interaction method:** microphone in the browser. Audio is captured as
  WebM/Opus, uploaded to the FastAPI backend, converted to 16 kHz mono WAV
  via FFmpeg, and transcribed by the N-ATLaS ASR model.
- **Recording:** every interaction is logged as a single JSON line in
  `docs/validation/interactions.jsonl`. Each record includes the transcript,
  the answer, per-stage timings, provider names, and (when given) the
  student's feedback on usefulness.

## Limitations

- **Hausa speech input is not validated end-to-end.** The ASR model used
  in this session (`NCAIR1/NigerianAccentedEnglish`) is trained on English.
  Hausa text answers were verified separately on the same N-ATLaS LLM.
  Validating Hausa speech requires swapping the ASR model to
  `NCAIR1/Hausa-ASR` — a one-line change to the ASR adapter configuration.
- **Single-machine session.** All interactions were recorded on one laptop.
  The pipeline is transport-agnostic; the same code has been verified to
  serve a browser on a different machine over the local network.
- **Self-reported feedback.** Usefulness ratings were provided by the
  students who asked the questions. There is no external judge.

## Evidence

- Full interaction log: `docs/validation/interactions.jsonl`
- Video demonstration: see `docs/SUBMISSION_URLS.txt`
- Source code: https://github.com/khalifa-4619/voice-education-assistant

"""

OUT.write_text(doc, encoding="utf-8")
print(f"Wrote {OUT}")
print(f"  interactions: {len(asks)}")
print(f"  feedbacks:    {len(feedbacks)}")
print(f"  useful:       {useful_true}")
print(f"  not useful:   {useful_false}")
print(f"  useful rate:  {useful_true / max(1, useful_true + useful_false) * 100:.0f}%")
