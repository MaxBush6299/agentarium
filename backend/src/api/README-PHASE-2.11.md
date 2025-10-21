# Phase 2.11: Agent Chat API & Streaming

## Overview
Phase 2.11 implements a production-ready RESTful Chat API with Server-Sent Events (SSE) streaming, conversation persistence, and trace logging.

## Features Implemented

### 1. Persistence Layer
- **Thread Management**: Conversation threads with message history
- **Run Tracking**: Execution tracking with status (QUEUED → IN_PROGRESS → COMPLETED/FAILED)
- **Step Tracing**: Tool call and message step tracking with latency and tokens
- **Cosmos DB Integration**: Async repositories with CRUD operations

**Files:**
- `src/persistence/models.py` - Pydantic models (Thread, Run, Step, Message, ToolCall)
- `src/persistence/threads.py` - Thread repository with soft delete, pagination
- `src/persistence/runs.py` - Run repository with status management, token tracking
- `src/persistence/steps.py` - Step repository with tool call tracing

### 2. SSE Streaming Infrastructure
- **EventGenerator**: Async queue-based SSE stream generator
- **Event Types**: token, trace_start, trace_update, trace_end, done, error, heartbeat
- **Features**:
  - Automatic heartbeat (15s) to prevent connection timeout
  - Buffering (10 events) and flush interval (0.1s)
  - Proper SSE format: `data: {json}\n\n`

**Files:**
- `src/api/streaming.py` - StreamEvent classes and EventGenerator

### 3. Chat API Endpoints
- **POST `/api/agents/{agent_id}/chat`**: Stream chat response with SSE
- **GET `/api/agents/{agent_id}/threads`**: List threads with pagination
- **GET `/api/agents/{agent_id}/threads/{thread_id}`**: Get thread details
- **DELETE `/api/agents/{agent_id}/threads/{thread_id}`**: Delete thread (soft/hard)

**Files:**
- `src/api/chat.py` - Chat router with 4 endpoints
- `src/main.py` - Router registration

## API Usage

### Start a Chat Conversation

```bash
curl -X POST http://localhost:8000/api/agents/support-triage/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "How do I create a storage account in Azure?",
    "stream": true
  }'
```

**SSE Response Format:**
```
data: {"type":"token","content":"To ","timestamp":"2024-01-15T10:30:00Z"}

data: {"type":"token","content":"create ","timestamp":"2024-01-15T10:30:00Z"}

data: {"type":"trace_start","step_id":"step_abc123","tool_name":"microsoft_docs_search","tool_type":"mcp","input":{"query":"Azure Storage Account"},"timestamp":"2024-01-15T10:30:01Z"}

data: {"type":"trace_end","step_id":"step_abc123","status":"completed","output":{"results":[...]},"latency_ms":245,"tokens":{"input":15,"output":20,"total":35},"timestamp":"2024-01-15T10:30:01Z"}

data: {"type":"done","run_id":"run_xyz789","thread_id":"thread_456","message_id":"msg_abc","tokens_used":150,"timestamp":"2024-01-15T10:30:02Z"}
```

### List Threads

```bash
curl http://localhost:8000/api/agents/support-triage/threads?limit=10&offset=0
```

**Response:**
```json
{
  "threads": [
    {
      "id": "thread_abc123",
      "agent_id": "support-triage",
      "title": "How do I create a storage account?",
      "status": "active",
      "messages": [...],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

### Get Thread Details

```bash
curl http://localhost:8000/api/agents/support-triage/threads/thread_abc123
```

### Delete Thread

```bash
# Soft delete (default)
curl -X DELETE http://localhost:8000/api/agents/support-triage/threads/thread_abc123

# Hard delete
curl -X DELETE http://localhost:8000/api/agents/support-triage/threads/thread_abc123?hard_delete=true
```

## Testing

### Manual Testing Script
```bash
# Start backend server
cd backend
python -m uvicorn src.main:app --reload

# In another terminal, run test script
python tests/manual/test_chat_api.py
```

The test script will:
1. Send a message to the support-triage agent
2. Display streaming tokens in real-time
3. Show trace events for tool calls
4. List all threads after completion

### Interactive Testing (Swagger UI)
1. Start server: `python src/main.py`
2. Open browser: `http://localhost:8000/docs`
3. Try the `/api/agents/{agent_id}/chat` endpoint

## Architecture

### Request Flow
```
Client Request
  ↓
POST /api/agents/{agent_id}/chat
  ↓
get_agent(agent_id) → SupportTriageAgent/AzureOpsAgent
  ↓
Get or Create Thread (Cosmos DB)
  ↓
Add User Message to Thread
  ↓
Create Run (status=IN_PROGRESS)
  ↓
stream_chat_response()
  ├── agent.base_agent.run_stream(message, thread)
  ├── EventGenerator → SSE Events
  │   ├── TokenEvent (text chunks)
  │   ├── TraceStartEvent (tool call start)
  │   ├── TraceEndEvent (tool call end)
  │   └── DoneEvent (completion)
  ├── Create Step records for tool calls
  ├── Add Assistant Message to Thread
  └── Update Run (status=COMPLETED, tokens)
  ↓
StreamingResponse → Client
```

### Data Model
```
Thread (1) ──┬── Messages (N)
             └── Runs (N)
                   │
                   └── Steps (N)
                         │
                         └── ToolCall (0..1)
```

## Known Limitations (MVP)

1. **Tool Call Tracing**: Currently streams text tokens only
   - TODO: Implement trace events for tool calls
   - Need to inspect `AgentRunResponseUpdate` for function_call property
   - Will capture: tool name, type, input, output, latency, tokens

2. **Thread Persistence**: Creates new agent framework thread each time
   - TODO: Serialize and restore agent framework threads
   - Need to: Store thread state in Cosmos DB
   - Need to: Restore thread state on continuation

3. **Token Counting**: Uses rough word-based estimation
   - TODO: Use actual token counts from Azure OpenAI response
   - Need to: Extract usage metadata from AgentRunResponse

4. **Agent Discovery**: Hardcoded agent_id mapping
   - TODO: Dynamic agent registry
   - Will be implemented in Phase 2.12

## Next Steps (Phase 2.11 Enhancements)

1. **Implement Tool Call Tracing**
   - Research `AgentRunResponseUpdate` properties
   - Detect tool call start/end in stream
   - Create Step records with tool metadata
   - Emit TraceStartEvent and TraceEndEvent

2. **Thread State Persistence**
   - Serialize agent framework thread to dict
   - Store thread state in Thread.metadata
   - Restore thread state on thread continuation
   - Test multi-turn conversations

3. **Token Counting**
   - Extract usage from AgentRunResponse
   - Update Run with actual token counts
   - Calculate costs based on model pricing

4. **Integration Tests**
   - Test chat streaming with support-triage agent
   - Test chat streaming with ops-assistant agent
   - Test thread continuation (multi-turn)
   - Test error handling (invalid agent_id, etc.)

## Next Phase: 2.12 - Agent Management API

After completing Phase 2.11 enhancements, implement:
- GET /api/agents - List all agents with capabilities
- GET /api/agents/{agent_id} - Get agent details
- POST /api/agents - Create new agent (admin)
- PUT /api/agents/{agent_id} - Update agent (admin)
- DELETE /api/agents/{agent_id} - Delete agent (admin)
- Agent seeding script for defaults

## Dependencies

**Python Packages:**
- fastapi - Web framework
- httpx - Async HTTP client
- pydantic - Data validation
- azure-cosmos - Cosmos DB SDK
- agent_framework - Microsoft Agent Framework

**Azure Services:**
- Cosmos DB (threads, runs, steps containers)
- Azure OpenAI (GPT-4o model)
- Key Vault (secrets management)

## Configuration

**Environment Variables:**
```env
# Cosmos DB
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_DATABASE_NAME=agent-demo
COSMOS_KEY=<primary-key>  # Or use connection string
COSMOS_CONNECTION_STRING=<connection-string>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Application
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=dev
LOCAL_DEV_MODE=true
```

## Completion Status

- [x] Persistence models (Thread, Run, Step, Message, ToolCall)
- [x] Thread repository with CRUD operations
- [x] Run repository with status management
- [x] Step repository with tool call tracking
- [x] SSE streaming infrastructure (EventGenerator)
- [x] Chat API endpoints (4 endpoints)
- [x] Router registration in main.py
- [x] Manual test script
- [ ] Tool call tracing (TODO - next iteration)
- [ ] Thread state persistence (TODO - next iteration)
- [ ] Actual token counting (TODO - next iteration)
- [ ] Integration tests (TODO - next iteration)

**Phase 2.11 Core: ✅ COMPLETE (MVP)**  
**Phase 2.11 Enhancements: 🔄 TODO (Next iteration)**
