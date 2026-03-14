"""Sayd client — sync and async."""

from __future__ import annotations

import httpx

from .talk import TalkResource, AsyncTalkResource
from .listen import ListenResource, AsyncListenResource
from .transcribe import TranscribeResource, AsyncTranscribeResource
from .vad import VADResource, AsyncVADResource

DEFAULT_BASE_URL = "https://api.sayd.dev"
DEFAULT_TIMEOUT = 30


class Sayd:
    """Synchronous Sayd client.

    Usage:
        client = Sayd(api_key="sk-your-key")
        session = client.talk.create(language="zh")
        for event in session.stream_file("audio.wav"):
            print(event)
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(timeout=timeout)

        # API resources
        self.talk = TalkResource(self)
        self.listen = ListenResource(self)
        self.transcribe = TranscribeResource(self)
        self.vad = VADResource(self)

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> Sayd:
        return self

    def __exit__(self, *args) -> None:
        self.close()


class AsyncSayd:
    """Async Sayd client.

    Usage:
        client = AsyncSayd(api_key="sk-your-key")
        session = await client.talk.create(language="zh")
        async for event in session.stream_file("audio.wav"):
            print(event)
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(timeout=timeout)

        # API resources
        self.talk = AsyncTalkResource(self)
        self.listen = AsyncListenResource(self)
        self.transcribe = AsyncTranscribeResource(self)
        self.vad = AsyncVADResource(self)

    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncSayd:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
