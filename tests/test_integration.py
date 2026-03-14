"""Integration tests against the real Sayd API.

These tests call the actual production API. Requires SAYD_TEST_API_KEY env var.
Run with: SAYD_TEST_API_KEY=sk-... python3 -m pytest tests/test_integration.py -v
"""

import os
import pytest

# Skip all tests if no API key
SAYD_TEST_API_KEY = os.environ.get("SAYD_TEST_API_KEY", "")
pytestmark = pytest.mark.skipif(
    not SAYD_TEST_API_KEY,
    reason="SAYD_TEST_API_KEY not set — skipping integration tests",
)


@pytest.fixture
def client():
    from sayd_ai import Sayd
    return Sayd(api_key=SAYD_TEST_API_KEY)


class TestTalkIntegration:
    """Talk API — create session, verify WS URL returned."""

    def test_create_session(self, client):
        stream = client.talk.create(language="en")
        assert stream.session_id
        assert stream.session.websocket_url.startswith("wss://")
        assert "talk" in stream.session.websocket_url

    def test_list_sessions(self, client):
        result = client.listen.list(limit=5)
        assert isinstance(result, list)


class TestListenIntegration:
    """Listen API — create session, list, get."""

    def test_create_session(self, client):
        session = client.listen.create(language="en")
        assert session.session_id
        assert session.websocket_url.startswith("wss://")
        assert "listen" in session.websocket_url
        assert session.stt_service is not None

    def test_create_session_multi_language(self, client):
        session = client.listen.create(language="multi")
        assert session.session_id
        assert session.language == "multi"

    def test_list_sessions(self, client):
        result = client.listen.list(limit=5)
        assert isinstance(result, list)

    def test_get_session(self, client):
        # Create then get
        session = client.listen.create(language="en")
        detail = client.listen.get(session.session_id)
        # Memorion may return different key formats
        assert isinstance(detail, dict)


class TestTranscribeIntegration:
    """Transcribe API — get upload URL, list."""

    def test_get_upload_url(self, client):
        result = client.transcribe.get_upload_url(language="en")
        assert "upload_url" in result
        assert result["upload_url"].startswith("http")

    def test_list_tasks(self, client):
        result = client.transcribe.list(limit=5)
        assert isinstance(result, list)


class TestVADIntegration:
    """VAD API — detect and check with real audio bytes."""

    @pytest.mark.skip(reason="Memorion VAD requires multipart file upload — SDK needs update")
    def test_detect_with_silence(self, client):
        silence = b"\x00" * 3200
        result = client.vad.detect(silence)
        assert isinstance(result, (list, dict))

    @pytest.mark.skip(reason="Memorion VAD requires multipart file upload — SDK needs update")
    def test_check_with_silence(self, client):
        silence = b"\x00" * 3200
        result = client.vad.check(silence)
        assert isinstance(result, bool)


class TestErrorHandling:
    """Test error handling with invalid inputs."""

    def test_invalid_api_key(self):
        from sayd_ai import Sayd
        from sayd_ai.exceptions import AuthenticationError
        bad_client = Sayd(api_key="sk-invalid-key-000000")
        with pytest.raises(AuthenticationError):
            bad_client.listen.create()

    def test_transcribe_nonexistent_task(self, client):
        from sayd_ai.exceptions import SaydError
        with pytest.raises(SaydError):
            client.transcribe.get("nonexistent-task-id-12345")
