"""Listen API — real-time speech-to-text (no cleaning)."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .models import ListenSession
from .exceptions import SaydError

if TYPE_CHECKING:
    from .client import Sayd, AsyncSayd


class ListenResource:
    """Synchronous Listen API resource."""

    def __init__(self, client: Sayd):
        self._client = client

    def create(
        self,
        *,
        language: str = "multi",
        sample_rate: int = 16000,
        codec: str = "pcm16",
    ) -> ListenSession:
        """Create a new real-time STT session.

        Args:
            language: Language code - "en", "zh", or "multi" (auto-detect)
            sample_rate: Audio sample rate in Hz (8000 or 16000)
            codec: Audio codec - "pcm16", "opus", or "opus_fs320"

        Returns:
            A ListenSession with session_id and websocket_url for direct connection.
        """
        response = self._client._http.post(
            f"{self._client.base_url}/api/listen",
            json={
                "language": language,
                "sample_rate": sample_rate,
                "codec": codec,
            },
            headers={"Authorization": self._client.api_key},
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code == 429:
            from .exceptions import RateLimitError
            raise RateLimitError()
        elif response.status_code != 200:
            raise SaydError(f"Failed to create listen session: {response.text}", response.status_code)

        return ListenSession.from_dict(response.json())

    def list(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List previous Listen sessions."""
        response = self._client._http.get(
            f"{self._client.base_url}/api/listen",
            params={"limit": limit, "offset": offset},
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Failed to list sessions: {response.text}", response.status_code)
        return response.json()

    def get(self, session_id: str) -> dict[str, Any]:
        """Get a Listen session with transcripts."""
        response = self._client._http.get(
            f"{self._client.base_url}/api/listen/{session_id}",
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Session not found: {response.text}", response.status_code)
        return response.json()


class AsyncListenResource:
    """Async Listen API resource."""

    def __init__(self, client: AsyncSayd):
        self._client = client

    async def create(
        self,
        *,
        language: str = "multi",
        sample_rate: int = 16000,
        codec: str = "pcm16",
    ) -> ListenSession:
        """Create a new real-time STT session (async)."""
        response = await self._client._http.post(
            f"{self._client.base_url}/api/listen",
            json={
                "language": language,
                "sample_rate": sample_rate,
                "codec": codec,
            },
            headers={"Authorization": self._client.api_key},
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code == 429:
            from .exceptions import RateLimitError
            raise RateLimitError()
        elif response.status_code != 200:
            raise SaydError(f"Failed to create listen session: {response.text}", response.status_code)

        return ListenSession.from_dict(response.json())

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List previous Listen sessions (async)."""
        response = await self._client._http.get(
            f"{self._client.base_url}/api/listen",
            params={"limit": limit, "offset": offset},
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Failed to list sessions: {response.text}", response.status_code)
        return response.json()

    async def get(self, session_id: str) -> dict[str, Any]:
        """Get a Listen session with transcripts (async)."""
        response = await self._client._http.get(
            f"{self._client.base_url}/api/listen/{session_id}",
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Session not found: {response.text}", response.status_code)
        return response.json()
