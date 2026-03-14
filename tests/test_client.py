"""Tests for Sayd client initialization and configuration."""

import pytest
from sayd_ai import Sayd, AsyncSayd


class TestSaydClient:
    """Test Sayd client initialization."""

    def test_create_with_api_key(self):
        client = Sayd(api_key="sk-test-key")
        assert client.api_key == "sk-test-key"
        assert client.base_url == "https://api.sayd.dev"

    def test_create_with_custom_base_url(self):
        client = Sayd(api_key="sk-test", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"

    def test_has_talk_resource(self):
        client = Sayd(api_key="sk-test")
        assert hasattr(client, "talk")
        assert client.talk is not None

    def test_has_listen_resource(self):
        client = Sayd(api_key="sk-test")
        assert hasattr(client, "listen")
        assert client.listen is not None

    def test_has_transcribe_resource(self):
        client = Sayd(api_key="sk-test")
        assert hasattr(client, "transcribe")
        assert client.transcribe is not None

    def test_has_vad_resource(self):
        client = Sayd(api_key="sk-test")
        assert hasattr(client, "vad")
        assert client.vad is not None

    def test_context_manager(self):
        with Sayd(api_key="sk-test") as client:
            assert client.api_key == "sk-test"


class TestAsyncSaydClient:
    """Test AsyncSayd client initialization."""

    def test_create_with_api_key(self):
        client = AsyncSayd(api_key="sk-test-key")
        assert client.api_key == "sk-test-key"

    def test_has_all_resources(self):
        client = AsyncSayd(api_key="sk-test")
        assert hasattr(client, "talk")
        assert hasattr(client, "listen")
        assert hasattr(client, "transcribe")
        assert hasattr(client, "vad")
