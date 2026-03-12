"""Talk API — real-time speech-to-text with smart cleaning."""

from __future__ import annotations

import json
import struct
import time
import wave
from pathlib import Path
from typing import Any, Generator, AsyncGenerator, TYPE_CHECKING

import httpx
import websockets
import websockets.sync.client

from .models import TalkEvent, TalkSession
from .exceptions import SaydError, SessionError

if TYPE_CHECKING:
    from .client import Sayd, AsyncSayd

# Audio chunk size: 100ms at 16kHz, 16-bit mono = 3200 bytes
CHUNK_SIZE = 3200
CHUNK_DURATION = 0.1  # seconds


class TalkResource:
    """Synchronous Talk API resource."""

    def __init__(self, client: Sayd):
        self._client = client

    def create(
        self,
        *,
        language: str = "multi",
        sample_rate: int = 16000,
        codec: str = "pcm16",
        cleaning_level: str = "standard",
        output_format: str = "paragraph",
    ) -> SyncTalkStream:
        """Create a new Talk session.

        Args:
            language: Language code - "en", "zh", or "multi" (auto-detect)
            sample_rate: Audio sample rate in Hz (8000 or 16000)
            codec: Audio codec - "pcm16" or "opus"
            cleaning_level: Cleaning intensity - "light", "standard", "aggressive"
            output_format: Output format - "paragraph", "bullets", "raw"

        Returns:
            A SyncTalkStream that can stream audio and receive transcriptions.
        """
        response = self._client._http.post(
            f"{self._client.base_url}/api/talk",
            json={
                "language": language,
                "sample_rate": sample_rate,
                "codec": codec,
                "cleaning_level": cleaning_level,
                "output_format": output_format,
            },
            headers={"Authorization": self._client.api_key},
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code == 403:
            from .exceptions import SubscriptionError
            raise SubscriptionError(response.json().get("error", "Subscription not active"))
        elif response.status_code != 200:
            raise SaydError(f"Failed to create session: {response.text}", response.status_code)

        data = response.json()
        session = TalkSession.from_dict(data)
        return SyncTalkStream(session, self._client)

    def list(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List previous Talk sessions."""
        response = self._client._http.get(
            f"{self._client.base_url}/api/talk",
            params={"limit": limit, "offset": offset},
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Failed to list sessions: {response.text}", response.status_code)
        return response.json()

    def get(self, session_id: str) -> dict[str, Any]:
        """Get a specific Talk session with its transcript."""
        response = self._client._http.get(
            f"{self._client.base_url}/api/talk/{session_id}",
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Session not found: {response.text}", response.status_code)
        return response.json()


class SyncTalkStream:
    """A synchronous Talk streaming session.

    Use stream_file() or stream_microphone() to send audio and receive events.
    """

    def __init__(self, session: TalkSession, client: Sayd):
        self.session = session
        self._client = client
        self._start_time: float | None = None
        self._end_time: float | None = None

    @property
    def session_id(self) -> str:
        return self.session.session_id

    @property
    def duration_minutes(self) -> float:
        return self.session.duration_minutes

    @property
    def cost_usd(self) -> float:
        return self.session.cost_usd

    def stream_file(self, path: str | Path) -> Generator[TalkEvent, None, None]:
        """Stream audio from a WAV file and yield transcription events.

        Args:
            path: Path to a WAV audio file (16-bit PCM, mono)

        Yields:
            TalkEvent objects as they arrive from the server
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        with wave.open(str(path), "rb") as wf:
            if wf.getnchannels() != 1:
                raise ValueError("Audio must be mono (1 channel)")
            if wf.getsampwidth() != 2:
                raise ValueError("Audio must be 16-bit")

            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)

        chunk_bytes = int(sample_rate * 2 * CHUNK_DURATION)  # bytes per chunk

        with websockets.sync.client.connect(self.session.websocket_url) as ws:
            self._start_time = time.time()

            # Wait for ready
            msg = ws.recv()
            event = TalkEvent.from_dict(json.loads(msg))
            if event.type == "ready":
                yield event

            # Send audio in chunks
            offset = 0
            while offset < len(audio_data):
                chunk = audio_data[offset : offset + chunk_bytes]
                ws.send(chunk)
                offset += chunk_bytes

                # Check for incoming messages (non-blocking)
                try:
                    while True:
                        msg = ws.recv(timeout=0.01)
                        event = TalkEvent.from_dict(json.loads(msg))
                        yield event
                except TimeoutError:
                    pass

                time.sleep(CHUNK_DURATION)

            # Signal end
            ws.send(json.dumps({"type": "end"}))

            # Receive remaining events
            for msg in ws:
                event = TalkEvent.from_dict(json.loads(msg))
                yield event

                if event.type == "cleaned" and event.duration_ms:
                    self.session.duration_minutes = event.duration_ms / 60000
                if event.type in ("complete", "error"):
                    break

            self._end_time = time.time()

        # Report usage for billing
        self._report_usage()

    def stream_microphone(
        self, *, device_index: int | None = None
    ) -> Generator[TalkEvent, None, None]:
        """Stream audio from microphone in real-time.

        Requires the `audio` extra: pip install sayd-ai[audio]

        Args:
            device_index: PyAudio device index (None = default mic)

        Yields:
            TalkEvent objects as they arrive
        """
        try:
            import pyaudio
        except ImportError:
            raise ImportError(
                "Microphone streaming requires PyAudio. "
                "Install with: pip install sayd-ai[audio]"
            )

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK_SIZE // 2,  # frames, not bytes
        )

        try:
            with websockets.sync.client.connect(self.session.websocket_url) as ws:
                self._start_time = time.time()

                # Wait for ready
                msg = ws.recv()
                event = TalkEvent.from_dict(json.loads(msg))
                if event.type == "ready":
                    yield event

                print("🎙️  Recording... Press Ctrl+C to stop.")

                try:
                    while True:
                        audio_chunk = stream.read(CHUNK_SIZE // 2, exception_on_overflow=False)
                        ws.send(audio_chunk)

                        # Check for messages
                        try:
                            while True:
                                msg = ws.recv(timeout=0.01)
                                event = TalkEvent.from_dict(json.loads(msg))
                                yield event
                        except TimeoutError:
                            pass

                except KeyboardInterrupt:
                    print("\n🛑 Stopping...")

                # Signal end
                ws.send(json.dumps({"type": "end"}))

                # Receive remaining
                for msg in ws:
                    event = TalkEvent.from_dict(json.loads(msg))
                    yield event

                    if event.type == "cleaned" and event.duration_ms:
                        self.session.duration_minutes = event.duration_ms / 60000
                    if event.type in ("complete", "error"):
                        break

                self._end_time = time.time()

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        self._report_usage()

    def _report_usage(self) -> None:
        """Report session completion for billing."""
        if self.session.duration_minutes <= 0 and self._start_time and self._end_time:
            # Fallback: estimate from wall clock
            self.session.duration_minutes = (self._end_time - self._start_time) / 60

        duration_ms = int(self.session.duration_minutes * 60000)
        if duration_ms <= 0:
            return

        try:
            response = self._client._http.post(
                f"{self._client.base_url}/api/talk/complete",
                json={
                    "session_id": self.session.session_id,
                    "duration_ms": duration_ms,
                },
                headers={"Authorization": self._client.api_key},
            )
            if response.status_code == 200:
                data = response.json()
                self.session.cost_usd = data.get("cost_usd", 0)
        except Exception:
            pass  # Non-critical: billing failure shouldn't break the user


class AsyncTalkResource:
    """Async Talk API resource."""

    def __init__(self, client: AsyncSayd):
        self._client = client

    async def create(
        self,
        *,
        language: str = "multi",
        sample_rate: int = 16000,
        codec: str = "pcm16",
        cleaning_level: str = "standard",
        output_format: str = "paragraph",
    ) -> AsyncTalkStream:
        """Create a new Talk session (async version)."""
        response = await self._client._http.post(
            f"{self._client.base_url}/api/talk",
            json={
                "language": language,
                "sample_rate": sample_rate,
                "codec": codec,
                "cleaning_level": cleaning_level,
                "output_format": output_format,
            },
            headers={"Authorization": self._client.api_key},
        )

        if response.status_code == 401:
            from .exceptions import AuthenticationError
            raise AuthenticationError()
        elif response.status_code == 403:
            from .exceptions import SubscriptionError
            raise SubscriptionError(response.json().get("error", "Subscription not active"))
        elif response.status_code != 200:
            raise SaydError(f"Failed to create session: {response.text}", response.status_code)

        data = response.json()
        session = TalkSession.from_dict(data)
        return AsyncTalkStream(session, self._client)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List previous Talk sessions (async)."""
        response = await self._client._http.get(
            f"{self._client.base_url}/api/talk",
            params={"limit": limit, "offset": offset},
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Failed to list sessions: {response.text}", response.status_code)
        return response.json()

    async def get(self, session_id: str) -> dict[str, Any]:
        """Get a specific Talk session (async)."""
        response = await self._client._http.get(
            f"{self._client.base_url}/api/talk/{session_id}",
            headers={"Authorization": self._client.api_key},
        )
        if response.status_code != 200:
            raise SaydError(f"Session not found: {response.text}", response.status_code)
        return response.json()


class AsyncTalkStream:
    """An async Talk streaming session."""

    def __init__(self, session: TalkSession, client: AsyncSayd):
        self.session = session
        self._client = client

    @property
    def session_id(self) -> str:
        return self.session.session_id

    @property
    def duration_minutes(self) -> float:
        return self.session.duration_minutes

    @property
    def cost_usd(self) -> float:
        return self.session.cost_usd

    async def stream_file(self, path: str | Path) -> AsyncGenerator[TalkEvent, None]:
        """Stream audio from a WAV file (async version)."""
        import asyncio

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        with wave.open(str(path), "rb") as wf:
            if wf.getnchannels() != 1:
                raise ValueError("Audio must be mono (1 channel)")
            if wf.getsampwidth() != 2:
                raise ValueError("Audio must be 16-bit")
            sample_rate = wf.getframerate()
            audio_data = wf.readframes(wf.getnframes())

        chunk_bytes = int(sample_rate * 2 * CHUNK_DURATION)
        start_time = time.time()

        async with websockets.connect(self.session.websocket_url) as ws:
            # Wait for ready
            msg = await ws.recv()
            event = TalkEvent.from_dict(json.loads(msg))
            if event.type == "ready":
                yield event

            # Send chunks
            offset = 0
            while offset < len(audio_data):
                chunk = audio_data[offset : offset + chunk_bytes]
                await ws.send(chunk)
                offset += chunk_bytes

                try:
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
                        event = TalkEvent.from_dict(json.loads(msg))
                        yield event
                except asyncio.TimeoutError:
                    pass

                await asyncio.sleep(CHUNK_DURATION)

            # Signal end
            await ws.send(json.dumps({"type": "end"}))

            # Receive remaining
            async for msg in ws:
                event = TalkEvent.from_dict(json.loads(msg))
                yield event

                if event.type == "cleaned" and event.duration_ms:
                    self.session.duration_minutes = event.duration_ms / 60000
                if event.type in ("complete", "error"):
                    break

        end_time = time.time()
        if self.session.duration_minutes <= 0:
            self.session.duration_minutes = (end_time - start_time) / 60

        await self._report_usage()

    async def _report_usage(self) -> None:
        """Report session completion for billing (async)."""
        duration_ms = int(self.session.duration_minutes * 60000)
        if duration_ms <= 0:
            return

        try:
            response = await self._client._http.post(
                f"{self._client.base_url}/api/talk/complete",
                json={
                    "session_id": self.session.session_id,
                    "duration_ms": duration_ms,
                },
                headers={"Authorization": self._client.api_key},
            )
            if response.status_code == 200:
                data = response.json()
                self.session.cost_usd = data.get("cost_usd", 0)
        except Exception:
            pass
