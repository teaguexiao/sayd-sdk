# sayd-ai

> Voice Interface for AI Agents. You said it. Agents did it.

Official Python SDK for the [Sayd](https://sayd.dev) Speech API.

## Installation

```bash
pip install sayd-ai
```

## Quick Start

```python
from sayd_ai import Sayd

client = Sayd(api_key="sk-your-key")

# Talk: real-time transcription with AI cleaning
session = client.talk.create(language="multi")
for event in session.stream_microphone():
    if event.type == "cleaned":
        print(event.cleaned_text)

# Listen: real-time STT (no cleaning)
session = client.listen.create(language="en")
print(f"Connect to: {session.websocket_url}")

# Transcribe: upload audio files
result = client.transcribe.upload("recording.wav")

# VAD: voice activity detection
has_speech = client.vad.check("audio.wav")
segments = client.vad.detect("audio.wav")
```

## Talk API — Voice Input with AI Cleaning

```python
from sayd_ai import Sayd

client = Sayd(api_key="sk-your-key")
session = client.talk.create(
    language="zh",
    cleaning_level="standard",
    output_format="paragraph",
)

# Stream from file
for event in session.stream_file("recording.wav"):
    if event.type == "sentence":
        print(f"[live] {event.text}")
    elif event.type == "cleaned":
        print(f"[clean] {event.cleaned_text}")

# Or stream from microphone (requires: pip install sayd-ai[audio])
for event in session.stream_microphone():
    if event.type == "partial":
        print(f"\r  {event.text}", end="", flush=True)
    elif event.type == "cleaned":
        print(f"\n✨ {event.cleaned_text}")

print(f"Duration: {session.duration_minutes:.1f} min")
print(f"Cost: ${session.cost_usd:.4f}")
```

## Listen API — Real-time STT

Raw transcription without AI cleaning. You get a WebSocket URL and connect directly.

```python
import json
import websockets.sync.client
from sayd_ai import Sayd

client = Sayd(api_key="sk-your-key")
session = client.listen.create(language="en", sample_rate=16000)

with websockets.sync.client.connect(session.websocket_url) as ws:
    ready = json.loads(ws.recv())  # {"type": "ready"}

    ws.send(audio_bytes)  # send PCM16 chunks

    for msg in ws:
        data = json.loads(msg)
        if data["type"] == "partial":
            print(f"\r  {data['text']}", end="")
        elif data["type"] == "sentence":
            print(f"\n[final] {data['text']}")

# List & get sessions
sessions = client.listen.list(limit=10)
detail = client.listen.get(session.session_id)
```

## Transcribe API — File Upload

Upload audio files for async transcription.

```python
from sayd_ai import Sayd

client = Sayd(api_key="sk-your-key")

# Convenience: upload handles everything
result = client.transcribe.upload("meeting.wav", language="multi")

# Or manual flow: get upload URL, upload yourself
url_info = client.transcribe.get_upload_url(language="en")
# Upload to url_info["upload_url"] directly

# Poll for results
task = client.transcribe.get("task-id")
print(f"Status: {task['status']}")  # completed
print(f"Text: {task['text']}")

# List tasks
tasks = client.transcribe.list(limit=20)
```

## VAD API — Voice Activity Detection

```python
from sayd_ai import Sayd

client = Sayd(api_key="sk-your-key")

# Detect speech segments
segments = client.vad.detect("recording.wav")
for seg in segments:
    print(f"Speech: {seg['start']:.2f}s - {seg['end']:.2f}s")

# Quick check: has speech?
has_speech = client.vad.check("recording.wav")

# Also works with raw bytes
has_speech = client.vad.check(audio_bytes)
```

## Async Support

All resources have async counterparts:

```python
import asyncio
from sayd_ai import AsyncSayd

async def main():
    client = AsyncSayd(api_key="sk-your-key")

    # Async listen
    session = await client.listen.create(language="en")

    # Async transcribe
    result = await client.transcribe.upload("audio.wav")

    # Async VAD
    has_speech = await client.vad.check(b"\x00" * 3200)

asyncio.run(main())
```

## Configuration

```python
client = Sayd(
    api_key="sk-your-key",
    base_url="https://api.sayd.dev",  # default
    timeout=30,                        # request timeout in seconds
)
```

## API Reference

| Resource | Methods |
|----------|---------|
| `client.talk` | `create()`, `list()`, `get()` + stream helpers |
| `client.listen` | `create()`, `list()`, `get()` |
| `client.transcribe` | `upload()`, `get_upload_url()`, `list()`, `get()` |
| `client.vad` | `detect()`, `check()` |

## cURL Examples

Want to test the API directly? See [examples/curl-examples.md](examples/curl-examples.md).

## License

MIT
