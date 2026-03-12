# cURL Examples

> Test the Sayd API directly from your terminal.

Replace `sk-your-key` with your actual API key. Default base URL: `https://sayd.dev`

## Authentication

All requests require your API key in the `Authorization` header:

```bash
export SAYD_API_KEY="sk-your-key"
export SAYD_BASE_URL="https://sayd.dev"
```

---

## 1. Create a Talk Session

Create a new real-time transcription session and get back a WebSocket URL for streaming audio.

```bash
curl -X POST "${SAYD_BASE_URL}/api/talk" \
  -H "Authorization: ${SAYD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "sample_rate": 16000,
    "codec": "pcm16",
    "cleaning_level": "standard",
    "output_format": "paragraph"
  }'
```

**Response:**

```json
{
  "session_id": "talk_abc123",
  "websocket_url": "wss://sayd.dev/ws/talk_abc123",
  "language": "en",
  "stt_service": "soniox"
}
```

### Language Options

```bash
# Chinese
curl -X POST "${SAYD_BASE_URL}/api/talk" \
  -H "Authorization: ${SAYD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"language": "zh"}'

# Auto-detect (multilingual)
curl -X POST "${SAYD_BASE_URL}/api/talk" \
  -H "Authorization: ${SAYD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"language": "multi"}'
```

### Cleaning Levels

```bash
# Light cleaning — minimal edits, preserves filler words
curl -X POST "${SAYD_BASE_URL}/api/talk" \
  -H "Authorization: ${SAYD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"language": "en", "cleaning_level": "light"}'

# Aggressive cleaning — heavy rewrite for readability
curl -X POST "${SAYD_BASE_URL}/api/talk" \
  -H "Authorization: ${SAYD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"language": "en", "cleaning_level": "aggressive"}'
```

---

## 2. Stream Audio via WebSocket

After creating a session, connect to the WebSocket URL and send raw PCM audio.

```bash
# Using websocat (install: brew install websocat / cargo install websocat)
# Stream a WAV file (skip 44-byte header for raw PCM)
tail -c +45 recording.wav | websocat "${WEBSOCKET_URL}"
```

```bash
# Using wscat (install: npm install -g wscat)
wscat -c "${WEBSOCKET_URL}"
# Then send binary audio frames from another tool
```

### Signal End of Audio

Send a JSON message to indicate you're done streaming:

```bash
# In the WebSocket connection, send:
{"type": "end"}
```

### Expected WebSocket Events

```json
// Session ready
{"type": "ready"}

// Partial (interim) transcription
{"type": "partial", "text": "Hello wor", "is_final": false}

// Final sentence
{"type": "sentence", "text": "Hello world.", "confidence": 0.95, "is_final": true}

// Cleaned transcript (after sending "end")
{
  "type": "cleaned",
  "cleaned_text": "Hello world. This is a test.",
  "original_text": "Hello world um this is uh a test.",
  "changes": [
    {"from": "um", "to": ""},
    {"from": "uh", "to": ""}
  ],
  "duration_ms": 5200
}

// Session complete
{"type": "complete"}
```

---

## 3. Report Session Completion

Report usage after a session ends (for billing):

```bash
curl -X POST "${SAYD_BASE_URL}/api/talk/complete" \
  -H "Authorization: ${SAYD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "talk_abc123",
    "duration_ms": 5200
  }'
```

**Response:**

```json
{
  "session_id": "talk_abc123",
  "duration_minutes": 0.087,
  "cost_usd": 0.0002
}
```

---

## 4. List Talk Sessions

Retrieve your previous sessions with pagination:

```bash
# List recent sessions (default: 50)
curl -X GET "${SAYD_BASE_URL}/api/talk?limit=10&offset=0" \
  -H "Authorization: ${SAYD_API_KEY}"
```

**Response:**

```json
[
  {
    "session_id": "talk_abc123",
    "language": "en",
    "duration_minutes": 2.5,
    "cost_usd": 0.0053,
    "created_at": "2026-03-13T00:00:00Z"
  },
  {
    "session_id": "talk_def456",
    "language": "zh",
    "duration_minutes": 10.2,
    "cost_usd": 0.0214,
    "created_at": "2026-03-12T18:30:00Z"
  }
]
```

---

## 5. Get Session Details

Get a specific session with its full transcript:

```bash
curl -X GET "${SAYD_BASE_URL}/api/talk/talk_abc123" \
  -H "Authorization: ${SAYD_API_KEY}"
```

**Response:**

```json
{
  "session_id": "talk_abc123",
  "language": "en",
  "stt_service": "soniox",
  "cleaning_level": "standard",
  "duration_minutes": 2.5,
  "cost_usd": 0.0053,
  "transcript": {
    "raw": "Hello world um this is uh a test.",
    "cleaned": "Hello world. This is a test."
  },
  "created_at": "2026-03-13T00:00:00Z"
}
```

---

## 6. Check Usage

Query your usage history:

```bash
curl -X GET "${SAYD_BASE_URL}/api/usage" \
  -H "Authorization: ${SAYD_API_KEY}"
```

**Response:**

```json
{
  "total_minutes": 42.7,
  "total_cost_usd": 0.0897,
  "sessions": 15,
  "period": "2026-03-01/2026-03-31"
}
```

---

## 7. Billing Portal

Get a redirect URL to manage your subscription via Stripe:

```bash
curl -X POST "${SAYD_BASE_URL}/api/billing/portal" \
  -H "Authorization: ${SAYD_API_KEY}"
```

**Response:**

```json
{
  "url": "https://billing.stripe.com/p/session/..."
}
```

---

## End-to-End Example

A complete flow: create session → stream audio → get cleaned result.

```bash
#!/bin/bash
set -e

SAYD_API_KEY="sk-your-key"
SAYD_BASE_URL="https://sayd.dev"
AUDIO_FILE="recording.wav"

echo "=== 1. Create Talk Session ==="
RESPONSE=$(curl -s -X POST "${SAYD_BASE_URL}/api/talk" \
  -H "Authorization: ${SAYD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"language": "en", "cleaning_level": "standard"}')

SESSION_ID=$(echo "$RESPONSE" | jq -r '.session_id')
WS_URL=$(echo "$RESPONSE" | jq -r '.websocket_url')
echo "Session: ${SESSION_ID}"
echo "WebSocket: ${WS_URL}"

echo ""
echo "=== 2. Stream Audio (via websocat) ==="
echo "Run in another terminal:"
echo "  tail -c +45 ${AUDIO_FILE} | websocat '${WS_URL}'"
echo "  # Then send: {\"type\":\"end\"}"

echo ""
echo "=== 3. After streaming, check session ==="
echo "  curl -s '${SAYD_BASE_URL}/api/talk/${SESSION_ID}' -H 'Authorization: ${SAYD_API_KEY}' | jq ."

echo ""
echo "=== 4. Check usage ==="
echo "  curl -s '${SAYD_BASE_URL}/api/usage' -H 'Authorization: ${SAYD_API_KEY}' | jq ."
```

---

## Error Responses

| HTTP Code | Error | Description |
|-----------|-------|-------------|
| 401 | `AuthenticationError` | Invalid or missing API key |
| 403 | `SubscriptionError` | Subscription not active / credit exhausted |
| 429 | `RateLimitError` | Too many requests (check `Retry-After` header) |
| 500 | `ServerError` | Internal server error |

```bash
# Example: invalid API key
curl -s -X POST "${SAYD_BASE_URL}/api/talk" \
  -H "Authorization: invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}'

# Response:
# {"error": "Invalid or missing API key", "code": 401}
```
