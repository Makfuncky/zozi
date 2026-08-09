# Stream: Documentation Voice Chat

**Description**: Voice-enabled documentation chat that allows developers to ask questions about the codebase using natural language and receive answers with source references.

## Streams

### `start`
Start a voice documentation chat session.

```bash
kilocode stream start-documentation-voice-chat
```

**What it does**:
1. Initializes a voice-enabled chat session
2. Loads the current codebase context (file tree, recent changes)
3. Opens a WebSocket connection for real-time voice transcription
4. Dispatches queries to the codebase RAG pipeline (embeddings over source files)
5. Returns answers with file:line citations

### `query`
Send a text or transcribed query to the active session.

```
POST /api/documentation-voice-chat/query
```

**Parameters**:
- `session_id` (string): Active session identifier
- `query` (string): The question or command
- `mode` (string, optional): `"code_search"` (default), `"explain"`, `"refactor"`

**Returns**:
```json
{
  "answer": "The authentication middleware is in backend/middleware/auth.py:45...",
  "references": [
    {"file": "backend/middleware/auth.py", "line": 45, "snippet": "def verify_token(...)"},
    {"file": "backend/routers/auth.py", "line": 12, "snippet": "router.include_router(...)"}
  ]
}
```

### `end`
End a voice documentation chat session.

```bash
kilocode stream end-documentation-voice-chat --session <session_id>
```

## Architecture

```
┌──────────────┐    WebSocket     ┌──────────────────┐    RAG     ┌──────────────┐
│  Voice UI     │ ◄──────────────► │  Chat Session     │ ◄────────► │  Codebase    │
│  (Browser)    │                  │  Manager           │            │  Embeddings  │
└──────────────┘                  └──────────────────┘            └──────────────┘
       │                                    │                             │
       │ Audio                              │ Dispatch                     │
       ▼                                    ▼                             ▼
┌──────────────┐                  ┌──────────────────┐            ┌──────────────┐
│  Whisper /   │                  │  Response         │            │  Source File │
│  STT Service │                  │  Formatter        │            │  Index       │
└──────────────┘                  └──────────────────┘            └──────────────┘
```

## Dependencies
- `backend/services/documentation_voice_chat.py` — Session lifecycle
- `backend/routers/documentation_voice_chat.py` — HTTP + WebSocket endpoints
- `backend/services/codebase_rag.py` — Embedding search over source files
- Frontend: `components/admin/DocumentationVoiceChat.tsx`

## Configuration
| Variable | Default | Description |
|---|---|---|
| `DOC_VOICE_CHAT_ENABLED` | `true` | Enable/disable the feature |
| `DOC_VOICE_CHAT_MAX_SESSIONS` | `10` | Maximum concurrent sessions |
| `DOC_VOICE_CHAT_SESSION_TTL` | `3600` | Session idle timeout (seconds) |