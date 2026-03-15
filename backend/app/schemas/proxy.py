"""Schemas for Claude API proxy endpoints."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    type: Literal["text", "image", "tool_use", "tool_result"]
    text: str | None = None
    # Support additional fields for non-text content
    model_config = {"extra": "allow"}


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str | list[ContentBlock]


class MessagesRequest(BaseModel):
    model: str
    max_tokens: int = Field(..., gt=0)
    messages: list[Message]
    system: str | None = None
    stream: bool = False
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    top_k: int | None = Field(default=None, ge=0)
    stop_sequences: list[str] | None = None
    metadata: dict[str, Any] | None = None

    model_config = {"extra": "allow"}


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int


class MessagesResponse(BaseModel):
    id: str
    type: str = "message"
    role: str = "assistant"
    model: str
    content: list[dict[str, Any]]
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: Usage
