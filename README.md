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

# Create a talk session and transcribe audio
session = client.talk.create(language="zh", cleaning_level="standard")

# Stream audio from file
for event in session.stream_file("recording.wav"):
    if event.type == "sentence":
        print(f"[live] {event.text}")
    elif event.type == "cleaned":
        print(f"[clean] {event.cleaned_text}")

print(f"Duration: {session.duration_minutes:.1f} min")
print(f"Cost: ${session.cost_usd:.4f}")
```

## Real-time Microphone Streaming

```python
from sayd_ai import Sayd

client = Sayd(api_key="sk-your-key")
session = client.talk.create(language="en")

# Stream from microphone (requires pyaudio)
for event in session.stream_microphone():
    if event.type == "partial":
        print(f"\r  {event.text}", end="", flush=True)
    elif event.type == "sentence":
        print(f"\n[final] {event.text}")
    elif event.type == "cleaned":
        print(f"\n\n--- Cleaned Transcript ---")
        print(event.cleaned_text)
```

## Async Support

```python
import asyncio
from sayd_ai import AsyncSayd

async def main():
    client = AsyncSayd(api_key="sk-your-key")
    session = await client.talk.create(language="multi")

    async for event in session.stream_file("audio.wav"):
        if event.type == "cleaned":
            print(event.cleaned_text)

asyncio.run(main())
```

## cURL Examples

Want to test the API directly without the SDK? Check out our [cURL examples](examples/curl-examples.md) for all endpoints.

## Configuration

```python
client = Sayd(
    api_key="sk-your-key",
    base_url="https://sayd.dev",  # default
    timeout=30,                    # request timeout in seconds
)
```

## Talk Session Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | str | `"multi"` | Language: `en`, `zh`, `multi` |
| `sample_rate` | int | `16000` | Audio sample rate: 8000 or 16000 |
| `codec` | str | `"pcm16"` | Codec: `pcm16`, `opus` |
| `cleaning_level` | str | `"standard"` | `light`, `standard`, `aggressive` |
| `output_format` | str | `"paragraph"` | `paragraph`, `bullets`, `raw` |

## License

MIT
