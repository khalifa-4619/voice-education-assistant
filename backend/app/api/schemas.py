"""Pydantic schemas for the HTTP boundary.

These are the shapes that cross the wire. They are deliberately separate
from app.pipeline.PipelineResult: the dataclass is what the pipeline
returns internally, the Pydantic model is what the API promises to send
over HTTP. Keeping them separate means we can evolve each without
breaking the other.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class AskResponse(BaseModel):
    """Response body for POST /api/v1/ask."""

    transcript: str = Field(
        ..., description="ASR transcript of the uploaded audio."
    )
    answer: str = Field(
        ..., description="Educational answer produced by the LLM adapter."
    )
    asr_seconds: float = Field(
        ..., ge=0, description="ASR stage duration in seconds."
    )
    llm_seconds: float = Field(
        ..., ge=0, description="LLM stage duration in seconds."
    )
    total_seconds: float = Field(
        ..., ge=0, description="Total pipeline duration in seconds."
    )
    started_at: datetime = Field(
        ..., description="UTC timestamp when the pipeline started."
    )
