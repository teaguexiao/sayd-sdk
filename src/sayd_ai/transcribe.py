"""Transcribe API — offline audio file transcription."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union, TYPE_CHECKING

from .exceptions import SaydError

if TYPE_CHECKING:
    from .client import Sayd, AsyncSayd


class TranscribeResource:
    """Synchronous Transcribe API resource."""

    def __init__(self, client: Sayd):
        self._client = client

    def get_upload_url(self, *, language: str = "multi") -> dict[str, str]:
        """Get a pre-authorized URL to upload audio directly to Memorion.

        Args:
            language: Language code for transcription

        Returns:
            Dict with 'upload_url' and 'method' keys.
        """
        response = self._client._http.post(
            f"{self._client.base_url}/api/transcribe",
            json={"language": language},
            headers={"Authorization": self._client.api_key},
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code == 429:
            from .exceptions import RateLimitError
            raise RateLimitError()
        elif response.status_code != 200:
            raise SaydError(f"Failed to get upload URL: {response.text}", response.status_code)

        return response.json()

    def upload(self, file_path: Union[str, Path], *, language: str = "multi") -> dict[str, Any]:
        """Upload an audio file for transcription.

        Convenience method: gets a pre-authorized URL, then uploads the file directly.

        Args:
            file_path: Path to the audio file
            language: Language code for transcription

        Returns:
            Transcription task info from Memorion.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Step 1: Get upload URL
        url_info = self.get_upload_url(language=language)
        upload_url = url_info["upload_url"]

        # Step 2: Upload directly to Memorion
        with open(file_path, "rb") as f:
            response = self._client._http.post(
                upload_url,
                files={"file": (file_path.name, f, "audio/wav")},
            )

        if response.status_code != 200:
            raise SaydError(f"Upload failed: {response.text}", response.status_code)

        return response.json()

    def list(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List transcription tasks."""
        response = self._client._http.get(
            f"{self._client.base_url}/api/transcribe",
            params={"limit": limit, "offset": offset},
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Failed to list tasks: {response.text}", response.status_code)
        return response.json()

    def get(self, task_id: str) -> dict[str, Any]:
        """Get a transcription result."""
        response = self._client._http.get(
            f"{self._client.base_url}/api/transcribe/{task_id}",
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Task not found: {response.text}", response.status_code)
        return response.json()


class AsyncTranscribeResource:
    """Async Transcribe API resource."""

    def __init__(self, client: AsyncSayd):
        self._client = client

    async def get_upload_url(self, *, language: str = "multi") -> dict[str, str]:
        """Get a pre-authorized upload URL (async)."""
        response = await self._client._http.post(
            f"{self._client.base_url}/api/transcribe",
            json={"language": language},
            headers={"Authorization": self._client.api_key},
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code == 429:
            from .exceptions import RateLimitError
            raise RateLimitError()
        elif response.status_code != 200:
            raise SaydError(f"Failed to get upload URL: {response.text}", response.status_code)

        return response.json()

    async def upload(self, file_path: Union[str, Path], *, language: str = "multi") -> dict[str, Any]:
        """Upload an audio file for transcription (async)."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        url_info = await self.get_upload_url(language=language)
        upload_url = url_info["upload_url"]

        with open(file_path, "rb") as f:
            response = await self._client._http.post(
                upload_url,
                files={"file": (file_path.name, f, "audio/wav")},
            )

        if response.status_code != 200:
            raise SaydError(f"Upload failed: {response.text}", response.status_code)

        return response.json()

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List transcription tasks (async)."""
        response = await self._client._http.get(
            f"{self._client.base_url}/api/transcribe",
            params={"limit": limit, "offset": offset},
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Failed to list tasks: {response.text}", response.status_code)
        return response.json()

    async def get(self, task_id: str) -> dict[str, Any]:
        """Get a transcription result (async)."""
        response = await self._client._http.get(
            f"{self._client.base_url}/api/transcribe/{task_id}",
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Task not found: {response.text}", response.status_code)
        return response.json()
