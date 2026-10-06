"""FastAPI application for the Voice Education Assistant.

This module wires together the HTTP layer. It is intentionally thin:

- The pipeline is built once at startup (via app.dependencies) and stored
  on app.state.pipeline. Routes read it from there.
- Routes live in app.api.routes and are included as a router.
- CORS is configured explicitly for the local React dev server.

Business logic does not live here.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.dependencies import build_pipeline

_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the pipeline once, at server startup.

    Loading the real ASR adapter takes ~78 seconds on the dev laptop.
    Building per request would make every request pay that cost.
    """
    app.state.pipeline = build_pipeline()
    yield


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

app.include_router(router)
