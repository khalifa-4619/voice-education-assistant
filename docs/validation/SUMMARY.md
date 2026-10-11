# Real-World Validation Summary

**Project:** Voice Education Assistant
**Challenge:** NITDA/NCAIR National AI Innovation Challenge 2026
**Problem Statement:** 2 — Voice-First Access
**Domain:** Education
**Recording period:** 2026-10-10T14:18:23.872117+00:00 to 2026-10-10T18:58:08.205784+00:00

## Overview

We validated the Voice Education Assistant with 52 real interactions
recorded on a CPU-only Windows laptop. Each interaction consists of a student
speaking an educational question into the browser and receiving a spoken
answer produced by the N-ATLaS pipeline (ASR → LLM → TTS). The full pipeline
ran locally: no GPU, no cloud, no external inference API.

Of the 52 interactions, 47 received explicit feedback
from the student.

## Summary statistics

| Metric | Value |
|---|---|
| Total interactions recorded | 52 |
| Interactions with feedback | 47 |
| Interactions without feedback | 5 |
| Rated useful (Yes) | 40 |
| Rated not useful (No) | 7 |
| Useful rate (of feedback given) | 85% |

### Latency (per interaction)

| Stage | Average | Min total | Max total |
|---|---|---|---|
| ASR | 14.4 s | — | — |
| LLM | 48.0 s | — | — |
| Total pipeline | 62.5 s | 13.7 s | 278.1 s |

The large spread in total time is expected: the model generates answers of
variable length, and short factual answers complete much faster than long
explanatory ones.

### Languages recorded

- `en`: 47 interaction(s)

### Subjects covered

- `general`: 26 interaction(s)
- `social`: 8 interaction(s)
- `math`: 6 interaction(s)
- `other`: 3 interaction(s)
- `english`: 3 interaction(s)
- `science`: 1 interaction(s)

## Sample interactions

### A representative successful interaction

- **Transcript (ASR):** do you describe the concept of a life cycle?
- **Answer (LLM):** A life cycle refers to the stages of growth and development through which an organism passes from the beginning of its life to the end. The life cycle includes various stages such as fertilization, embryonic development, growth, reproduction, and death. In plants, the life cycle includes the stages of germination, growth, reproduction, and death. In animals, the life cycle includes the stages of …
- **Timings:** ASR 20.1s · LLM 38.2s · Total 58.3s
- **Student feedback:** useful

### A representative weaker interaction

- **Transcript (ASR):** what's the spectacularest theory?
- **Answer (LLM):** I'm sorry, I don't understand the question. Could you provide more details or rephrase it? Perhaps I can help if you clarify what you're asking about.
- **Timings:** ASR 22.5s · LLM 29.2s · Total 51.7s
- **Student feedback:** not useful

## Methodology

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

