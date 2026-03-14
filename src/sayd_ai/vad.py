"""VAD API — voice activity detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union, TYPE_CHECKING

from .exceptions import SaydError

if TYPE_CHECKING:
    from .client import Sayd, AsyncSayd


def _load_audio(audio: Union[str, Path, bytes]) -> bytes:
    """Load audio from file path or return raw bytes."""
    if isinstance(audio, bytes):
        return audio
    path = Path(audio)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    return path.read_bytes()


class VADResource:
    """Synchronous VAD (Voice Activity Detection) resource."""

    def __init__(self, client: Sayd):
        self._client = client

    def detect(self, audio: Union[str, Path, bytes]) -> list[dict[str, Any]]:
        """Detect speech segments in audio.

        Args:
            audio: Audio file path (str/Path) or raw audio bytes

        Returns:
            List of speech segments with start/end timestamps.
        """
        data = _load_audio(audio)
        response = self._client._http.post(
            f"{self._client.base_url}/api/vad",
            content=data,
            headers={
                "Authorization": self._client.api_key,
                "Content-Type": "application/octet-stream",
            },
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code != 200:
            raise SaydError(f"VAD detection failed: {response.text}", response.status_code)

        return response.json()

    def check(self, audio: Union[str, Path, bytes]) -> bool:
        """Check if audio contains speech.

        Args:
            audio: Audio file path (str/Path) or raw audio bytes

        Returns:
            True if speech is detected, False otherwise.
        """
        data = _load_audio(audio)
        response = self._client._http.post(
            f"{self._client.base_url}/api/vad/check",
            content=data,
            headers={
                "Authorization": self._client.api_key,
                "Content-Type": "application/octet-stream",
            },
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code != 200:
            raise SaydError(f"VAD check failed: {response.text}", response.status_code)

        result = response.json()
        return result.get("has_speech", False)


class AsyncVADResource:
    """Async VAD resource."""

    def __init__(self, client: AsyncSayd):
        self._client = client

    async def detect(self, audio: Union[str, Path, bytes]) -> list[dict[str, Any]]:
        """Detect speech segments (async)."""
        data = _load_audio(audio)
        response = await self._client._http.post(
            f"{self._client.base_url}/api/vad",
            content=data,
            headers={
                "Authorization": self._client.api_key,
                "Content-Type": "application/octet-stream",
            },
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code != 200:
            raise SaydError(f"VAD detection failed: {response.text}", response.status_code)

        return response.json()

    async def check(self, audio: Union[str, Path, bytes]) -> bool:
        """Check if audio contains speech (async)."""
        data = _load_audio(audio)
        response = await self._client._http.post(
            f"{self._client.base_url}/api/vad/check",
            content=data,
            headers={
                "Authorization": self._client.api_key,
                "Content-Type": "application/octet-stream",
            },
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code != 200:
            raise SaydError(f"VAD check failed: {response.text}", response.status_code)

        result = response.json()
        return result.get("has_speech", False)
