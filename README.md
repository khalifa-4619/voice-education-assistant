# Voice Education Assistant

Voice-first AI educational assistant for Nigerian secondary-school students.

Submitted to the **NITDA/NCAIR National AI Innovation Challenge 2026** under
**Problem Statement 2 — Voice-First Access**, domain: **Education**.

## Problem

Nigerian secondary-school students often cannot easily get clear, spoken
answers to educational questions. Text-only tools exclude students who are
more comfortable speaking than typing, and most tools do not respond in the
student's own language.

## Solution

A voice-first assistant:

    Student speaks
      -> N-ATLaS ASR (official)
      -> transcribed question
      -> N-ATLaS (educational answer)
      -> text-to-speech
      -> student hears the answer

Initial language targets: **Hausa** and **Nigerian-accented English**.

## Status

Milestone 0 — Project Foundation. In progress.

See `docs/` for milestone tracking and design notes.

## Repository layout

    backend/    Python / FastAPI backend and AI pipeline
    frontend/   React student-facing interface
    tests/      Test suites
    docs/       Design notes, milestone log, validation records

## Development

Backend uses Python 3.12 with a virtual environment at `backend/.venv/`.

    cd backend
    source .venv/bin/activate
    pip install -r requirements.txt

Environment variables are documented in `.env.example`. Copy it to `.env`
locally and fill in secrets. **Never commit `.env`.**

## License

TBD.
