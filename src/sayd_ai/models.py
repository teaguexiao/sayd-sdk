"""Data models for the Sayd SDK."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TalkEvent:
    """An event received from a Talk session WebSocket stream.

    Attributes:
        type: Event type - "ready", "partial", "sentence", "cleaned", "complete", "error"
        text: Transcript text (for partial/sentence events)
        cleaned_text: LLM-cleaned transcript (for cleaned events)
        original_text: Original raw transcript before cleaning (for cleaned events)
        changes: List of changes made during cleaning (for cleaned events)
        confidence: Transcription confidence score (for sentence events)
        is_final: Whether this is a final segment (for partial/sentence events)
        duration_ms: Session duration in milliseconds (for cleaned/complete events)
        raw: The raw JSON dict from the WebSocket message
    """

    type: str
    text: str | None = None
    cleaned_text: str | None = None
    original_text: str | None = None
    changes: list[dict[str, str]] | None = None
    confidence: float | None = None
    is_final: bool | None = None
    duration_ms: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TalkEvent:
        return cls(
            type=data.get("type", "unknown"),
            text=data.get("text"),
            cleaned_text=data.get("cleaned_text"),
            original_text=data.get("original_text"),
            changes=data.get("changes"),
            confidence=data.get("confidence"),
            is_final=data.get("is_final"),
            duration_ms=data.get("duration_ms"),
            raw=data,
        )


@dataclass
class TalkSession:
    """Metadata for a Talk session.

    Attributes:
        session_id: Unique session identifier
        websocket_url: WebSocket URL for streaming audio
        language: Language code used for transcription
        stt_service: STT service provider (e.g., "soniox")
        duration_minutes: Total transcription duration (set after completion)
        cost_usd: Billing cost in USD (set after completion)
    """

    session_id: str
    websocket_url: str
    language: str = "multi"
    stt_service: str | None = None
    duration_minutes: float = 0.0
    cost_usd: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TalkSession:
        return cls(
            session_id=data["session_id"],
            websocket_url=data["websocket_url"],
            language=data.get("language", "multi"),
            stt_service=data.get("stt_service"),
        )
