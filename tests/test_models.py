"""Tests for data models."""

import pytest
from sayd_ai.models import TalkEvent, TalkSession, ListenSession, TranscriptionTask


class TestTalkEvent:
    def test_from_dict_basic(self):
        event = TalkEvent.from_dict({"type": "ready"})
        assert event.type == "ready"
        assert event.text is None

    def test_from_dict_partial(self):
        event = TalkEvent.from_dict({
            "type": "partial",
            "text": "hello world",
            "is_final": False,
        })
        assert event.type == "partial"
        assert event.text == "hello world"
        assert event.is_final is False

    def test_from_dict_cleaned(self):
        event = TalkEvent.from_dict({
            "type": "cleaned",
            "cleaned_text": "Hello, world.",
            "original_text": "hello world um",
            "changes": [{"type": "filler_removal", "text": "um"}],
            "duration_ms": 5000,
        })
        assert event.type == "cleaned"
        assert event.cleaned_text == "Hello, world."
        assert event.original_text == "hello world um"
        assert event.duration_ms == 5000
        assert len(event.changes) == 1

    def test_from_dict_preserves_raw(self):
        raw = {"type": "complete", "extra_field": "value"}
        event = TalkEvent.from_dict(raw)
        assert event.raw == raw

    def test_from_dict_unknown_type(self):
        event = TalkEvent.from_dict({})
        assert event.type == "unknown"


class TestTalkSession:
    def test_from_dict(self):
        session = TalkSession.from_dict({
            "session_id": "sess-123",
            "websocket_url": "wss://example.com/ws",
            "language": "en",
            "stt_service": "deepgram",
        })
        assert session.session_id == "sess-123"
        assert session.websocket_url == "wss://example.com/ws"
        assert session.language == "en"
        assert session.stt_service == "deepgram"

    def test_from_dict_defaults(self):
        session = TalkSession.from_dict({
            "session_id": "sess-456",
            "websocket_url": "wss://example.com/ws",
        })
        assert session.language == "multi"
        assert session.stt_service is None
        assert session.duration_minutes == 0.0
        assert session.cost_usd == 0.0


class TestListenSession:
    def test_from_dict(self):
        session = ListenSession.from_dict({
            "session_id": "listen-001",
            "websocket_url": "wss://example.com/listen/ws",
            "language": "zh",
            "stt_service": "soniox",
        })
        assert session.session_id == "listen-001"
        assert session.websocket_url == "wss://example.com/listen/ws"
        assert session.language == "zh"
        assert session.stt_service == "soniox"

    def test_from_dict_defaults(self):
        session = ListenSession.from_dict({
            "session_id": "listen-002",
            "websocket_url": "wss://example.com/ws",
        })
        assert session.language == "multi"
        assert session.stt_service is None


class TestTranscriptionTask:
    def test_from_dict(self):
        task = TranscriptionTask.from_dict({
            "task_id": "task-abc",
            "status": "completed",
            "upload_url": "https://upload.example.com",
        })
        assert task.task_id == "task-abc"
        assert task.status == "completed"
        assert task.upload_url == "https://upload.example.com"

    def test_from_dict_with_id_fallback(self):
        task = TranscriptionTask.from_dict({
            "id": "task-xyz",
            "status": "processing",
        })
        assert task.task_id == "task-xyz"

    def test_from_dict_defaults(self):
        task = TranscriptionTask.from_dict({})
        assert task.task_id == ""
        assert task.status == "pending"
        assert task.upload_url is None
