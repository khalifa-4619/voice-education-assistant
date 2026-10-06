"""FastAPI application for the Voice Education Assistant.

This module defines the HTTP layer. It is intentionally thin:

- The pipeline is built once at startup (via the composition root in
  app.dependencies) and stored on app.state.pipeline.
- Routes depend on app.state.pipeline, never on a concrete ASR or LLM
  adapter. Swapping the model does not touch this file.
- CORS is configured explicitly for the local React dev server.

Business logic does not live here. If a route grows beyond "read request,
call pipeline, return response", the logic belongs in a service module
under app/services/ and the route should delegate to it.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import build_pipeline, describe_providers

# Origins permitted to call this API from a browser. In local development
# this is the Vite dev server (5173) and, for convenience, the Create React
# App default (3000). Production origins will be added when we deploy.
_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the pipeline once, at server startup.

    The pipeline is stored on app.state so every request shares the same
    instance. This matters for the real ASR adapter: loading Whisper Small
    takes ~78 seconds on the dev laptop. Building per request would make
    every request pay that cost.
    """
    app.state.pipeline = build_pipeline()
    yield
    # No cleanup needed yet. When we add a real LLM runtime, its teardown
    # goes here.


app = FastAPI(
    title="Voice Education Assistant API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEV_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Liveness probe. Reports status and the currently selected providers.

    This endpoint is used by local dev tooling and (later) by deployment
    health checks. It does not touch the pipeline.
    """
    return {
        "status": "ok",
        "providers": describe_providers(),
    }
