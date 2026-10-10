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

    interaction_id: str = Field(
        ...,
        description=(
            "Unique identifier for this interaction. Must be sent back to "
            "POST /api/v1/feedback if the student provides feedback."
        ),
    )
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


class FeedbackRequest(BaseModel):
    """Request body for POST /api/v1/feedback.

    Captures the student's self-reported assessment of one interaction.
    Used for the challenge's required validation record.
    """

    interaction_id: str = Field(
        ..., min_length=1, description="From the corresponding AskResponse."
    )
    useful: bool = Field(
        ..., description="Whether the student found the answer useful."
    )
    language: str = Field(
        default="en",
        description="Language the question was asked in, e.g. 'en', 'ha'.",
    )
    subject: str = Field(
        default="other",
        description="Subject area, e.g. 'science', 'math', 'english'.",
    )
    notes: str = Field(
        default="",
        max_length=2000,
        description="Optional free-text comments from the student.",
    )


class FeedbackResponse(BaseModel):
    """Response body for POST /api/v1/feedback."""

    recorded: bool
    interaction_id: str
