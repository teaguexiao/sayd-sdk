"""Tests for API resources using httpx mock transport."""

import json
import pytest
import httpx

from sayd_ai import Sayd
from sayd_ai.exceptions import AuthenticationError, RateLimitError, SaydError


def mock_transport(handler):
    """Create a mock httpx transport from a handler function."""
    return httpx.MockTransport(handler)


def json_response(data, status_code=200):
    """Build a JSON httpx.Response."""
    return httpx.Response(status_code, json=data)


def error_response(message, status_code):
    """Build an error httpx.Response."""
    return httpx.Response(status_code, json={"error": message})


class TestListenResource:
    def _client(self, handler):
        transport = mock_transport(handler)
        http = httpx.Client(transport=transport)
        client = Sayd(api_key="sk-test")
        client._http = http
        return client

    def test_create_success(self):
        def handler(request):
            assert request.method == "POST"
            assert "/api/listen" in str(request.url)
            body = json.loads(request.content)
            return json_response({
                "session_id": "listen-001",
                "websocket_url": "wss://api.memorion.me/ws/listen-001",
                "language": body.get("language", "multi"),
                "stt_service": "deepgram",
            })

        client = self._client(handler)
        session = client.listen.create(language="en")
        assert session.session_id == "listen-001"
        assert session.websocket_url == "wss://api.memorion.me/ws/listen-001"
        assert session.language == "en"

    def test_create_auth_error(self):
        def handler(request):
            return error_response("Invalid API key", 401)

        client = self._client(handler)
        with pytest.raises(AuthenticationError):
            client.listen.create()

    def test_create_rate_limit(self):
        def handler(request):
            return error_response("Rate limit exceeded", 429)

        client = self._client(handler)
        with pytest.raises(RateLimitError):
            client.listen.create()

    def test_list_success(self):
        def handler(request):
            assert request.method == "GET"
            return json_response([
                {"session_id": "listen-001", "created_at": "2026-03-14"},
                {"session_id": "listen-002", "created_at": "2026-03-13"},
            ])

        client = self._client(handler)
        sessions = client.listen.list(limit=10)
        assert len(sessions) == 2

    def test_get_success(self):
        def handler(request):
            assert "listen-001" in str(request.url)
            return json_response({
                "session_id": "listen-001",
                "transcripts": [{"text": "hello"}],
            })

        client = self._client(handler)
        result = client.listen.get("listen-001")
        assert result["session_id"] == "listen-001"


class TestTranscribeResource:
    def _client(self, handler):
        transport = mock_transport(handler)
        http = httpx.Client(transport=transport)
        client = Sayd(api_key="sk-test")
        client._http = http
        return client

    def test_get_upload_url_success(self):
        def handler(request):
            assert request.method == "POST"
            return json_response({
                "upload_url": "https://api2.memorion.me/upload/abc123",
                "method": "POST",
            })

        client = self._client(handler)
        result = client.transcribe.get_upload_url(language="en")
        assert "upload_url" in result
        assert result["upload_url"].startswith("https://")

    def test_get_upload_url_auth_error(self):
        def handler(request):
            return error_response("Unauthorized", 401)

        client = self._client(handler)
        with pytest.raises(AuthenticationError):
            client.transcribe.get_upload_url()

    def test_list_success(self):
        def handler(request):
            return json_response([{"task_id": "t-1", "status": "completed"}])

        client = self._client(handler)
        tasks = client.transcribe.list()
        assert len(tasks) == 1

    def test_get_success(self):
        def handler(request):
            return json_response({
                "task_id": "t-1",
                "status": "completed",
                "text": "Hello world",
                "duration_ms": 5000,
            })

        client = self._client(handler)
        result = client.transcribe.get("t-1")
        assert result["status"] == "completed"

    def test_upload_file_not_found(self):
        def handler(request):
            return json_response({})

        client = self._client(handler)
        with pytest.raises(FileNotFoundError):
            client.transcribe.upload("/nonexistent/audio.wav")


class TestVADResource:
    def _client(self, handler):
        transport = mock_transport(handler)
        http = httpx.Client(transport=transport)
        client = Sayd(api_key="sk-test")
        client._http = http
        return client

    def test_detect_with_bytes(self):
        def handler(request):
            assert request.method == "POST"
            assert request.headers["Content-Type"] == "application/octet-stream"
            assert request.headers["Authorization"] == "sk-test"
            return json_response([
                {"start": 0.5, "end": 2.3},
                {"start": 3.1, "end": 5.0},
            ])

        client = self._client(handler)
        segments = client.vad.detect(b"\x00" * 3200)
        assert len(segments) == 2
        assert segments[0]["start"] == 0.5

    def test_detect_file_not_found(self):
        def handler(request):
            return json_response([])

        client = self._client(handler)
        with pytest.raises(FileNotFoundError):
            client.vad.detect("/nonexistent/audio.wav")

    def test_check_with_bytes(self):
        def handler(request):
            return json_response({"has_speech": True})

        client = self._client(handler)
        result = client.vad.check(b"\x00" * 1600)
        assert result is True

    def test_check_no_speech(self):
        def handler(request):
            return json_response({"has_speech": False})

        client = self._client(handler)
        result = client.vad.check(b"\x00" * 1600)
        assert result is False

    def test_detect_auth_error(self):
        def handler(request):
            return error_response("Unauthorized", 401)

        client = self._client(handler)
        with pytest.raises(AuthenticationError):
            client.vad.detect(b"\x00" * 100)

    def test_detect_with_temp_file(self, tmp_path):
        """Test detect with an actual file path."""
        audio_file = tmp_path / "test.pcm"
        audio_file.write_bytes(b"\x00" * 3200)

        def handler(request):
            return json_response([{"start": 0.0, "end": 0.2}])

        client = self._client(handler)
        segments = client.vad.detect(str(audio_file))
        assert len(segments) == 1

    def test_check_with_temp_file(self, tmp_path):
        """Test check with an actual file path."""
        audio_file = tmp_path / "test.pcm"
        audio_file.write_bytes(b"\x00" * 1600)

        def handler(request):
            return json_response({"has_speech": False})

        client = self._client(handler)
        assert client.vad.check(str(audio_file)) is False


class TestVersionAndExports:
    def test_version(self):
        import sayd_ai
        assert sayd_ai.__version__ == "0.2.0"

    def test_exports(self):
        from sayd_ai import (
            Sayd, AsyncSayd,
            TalkEvent, TalkSession,
            ListenSession, TranscriptionTask,
            SaydError, AuthenticationError, RateLimitError,
        )
        # All imports should succeed
        assert Sayd is not None
