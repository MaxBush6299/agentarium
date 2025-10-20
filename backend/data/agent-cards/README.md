# Agent Card Storage System

## Overview

The Agent Card Storage System provides persistent file-based storage for A2A Protocol agent cards. This enables dynamic agent registration, discovery, and management through both the A2A protocol and REST API.

## Architecture

### Components

1. **AgentCardStore** (`backend/src/a2a/agent_cards.py`)
   - File-based storage for agent cards
   - CRUD operations for agent metadata
   - Combined card generation for multi-agent discovery
   - Validation against A2A protocol specification

2. **Agent Card Management API** (`backend/src/a2a/api.py`)
   - REST API for creating, updating, and deleting agent cards
   - Frontend integration for dynamic agent registration
   - Endpoints for listing and retrieving agent cards

3. **Storage Directory** (`backend/data/agent-cards/`)
   - JSON files for each registered agent
   - One file per agent: `{agent_id}.json`
   - Human-readable and version-control friendly

### File Structure

```
backend/
├── data/
│   └── agent-cards/
│       ├── support-triage.json
│       ├── ops-assistant.json
│       ├── sql-query.json
│       └── {agent-id}.json
├── src/
│   └── a2a/
│       ├── agent_cards.py    # Storage implementation
│       ├── api.py            # Management API
│       └── server.py         # A2A protocol server
```

## Storage Format

Each agent card is stored as a JSON file conforming to the A2A Protocol specification:

```json
{
  "protocolVersion": "0.3.0",
  "name": "Support Triage Agent",
  "description": "AI agent for triaging customer support requests...",
  "url": "http://localhost:8000/a2a",
  "preferredTransport": "JSONRPC",
  "version": "1.0.0",
  "provider": "Multi-Agent Demo",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "stateTransitionHistory": false
  },
  "skills": [
    {
      "id": "support-triage",
      "name": "Support Request Triage",
      "description": "Analyzes customer support requests...",
      "tags": ["support", "triage", "azure"],
      "examples": [
        "How do I deploy a Python FastAPI application to Azure?"
      ]
    }
  ],
  "metadata": {
    "agent_id": "support-triage",
    "last_updated": "2025-10-20T00:00:00Z",
    "created_at": "2025-10-20T00:00:00Z",
    "source": "default"
  }
}
```

## API Endpoints

### List All Agent Cards

```http
GET /api/agent-cards/
```

**Response:**
```json
{
  "agent_ids": ["support-triage", "ops-assistant"],
  "count": 2
}
```

### Get Specific Agent Card

```http
GET /api/agent-cards/{agent_id}
```

**Response:**
```json
{
  "agent_id": "support-triage",
  "card": { /* agent card object */ }
}
```

### Create Agent Card

```http
POST /api/agent-cards/
Content-Type: application/json

{
  "agent_id": "new-agent",
  "name": "New Agent",
  "description": "Agent description",
  "base_url": "http://localhost:8000",
  "skills": [
    {
      "id": "skill-1",
      "name": "Skill Name",
      "description": "Skill description",
      "tags": ["tag1", "tag2"],
      "examples": ["Example 1", "Example 2"]
    }
  ],
  "provider": "My Organization",
  "version": "1.0.0"
}
```

**Response:** 201 Created
```json
{
  "agent_id": "new-agent",
  "card": { /* created agent card */ }
}
```

### Update Agent Card

```http
PUT /api/agent-cards/{agent_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "skills": [ /* updated skills */ ]
}
```

**Response:** 200 OK

### Delete Agent Card

```http
DELETE /api/agent-cards/{agent_id}
```

**Response:** 204 No Content

### Get Combined Agent Card

```http
GET /api/agent-cards/.well-known/combined?base_url=http://localhost:8000
```

Returns a single agent card combining all registered agents as skills.

## Usage Examples

### Python: Creating an Agent Card Programmatically

```python
from src.a2a.agent_cards import get_agent_card_store, AgentCard, AgentSkill, AgentCapabilities

# Get the store
store = get_agent_card_store()

# Create agent card
card = AgentCard(
    name="Custom Agent",
    description="A custom agent",
    url="http://localhost:8000/a2a",
    version="1.0.0",
    provider="My Org",
    capabilities=AgentCapabilities(
        streaming=False,
        pushNotifications=False,
        stateTransitionHistory=False
    ),
    skills=[
        AgentSkill(
            id="custom-skill",
            name="Custom Skill",
            description="Does something useful",
            tags=["custom", "demo"],
            examples=["Example query"]
        )
    ]
)

# Save to storage
store.save_agent_card("custom-agent", card)
```

### Python: Using the Helper Method

```python
from src.a2a.agent_cards import get_agent_card_store

store = get_agent_card_store()

# Create from config dict
store.create_agent_from_config(
    agent_id="quick-agent",
    name="Quick Agent",
    description="Created quickly",
    skills=[
        {
            "id": "skill-1",
            "name": "Skill Name",
            "description": "Skill description",
            "tags": ["tag1"],
            "examples": ["Example"]
        }
    ],
    base_url="http://localhost:8000",
    provider="Demo Org",
    version="1.0.0"
)
```

### TypeScript/Frontend: Creating Agent Card via API

```typescript
interface CreateAgentCardRequest {
  agent_id: string;
  name: string;
  description: string;
  base_url: string;
  skills: Array<{
    id: string;
    name: string;
    description: string;
    tags: string[];
    examples: string[];
  }>;
  provider?: string;
  version?: string;
}

async function createAgentCard(request: CreateAgentCardRequest) {
  const response = await fetch('http://localhost:8000/api/agent-cards/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create agent card: ${response.statusText}`);
  }
  
  return response.json();
}

// Usage
const newAgent = await createAgentCard({
  agent_id: 'my-custom-agent',
  name: 'My Custom Agent',
  description: 'Agent created from frontend',
  base_url: 'http://localhost:8000',
  skills: [
    {
      id: 'custom-skill',
      name: 'Custom Skill',
      description: 'Does something useful',
      tags: ['custom', 'frontend'],
      examples: ['Example query 1', 'Example query 2'],
    },
  ],
  provider: 'My Organization',
  version: '1.0.0',
});

console.log('Agent created:', newAgent);
```

### TypeScript: Listing All Agents

```typescript
async function listAgentCards() {
  const response = await fetch('http://localhost:8000/api/agent-cards/');
  const data = await response.json();
  
  console.log(`Found ${data.count} agents:`, data.agent_ids);
  return data;
}
```

## A2A Protocol Integration

The agent card storage system integrates seamlessly with the A2A protocol:

1. **Discovery Endpoint** (`/.well-known/agent.json`)
   - Automatically generates combined agent card from storage
   - Lists all registered agents as skills
   - Updates dynamically when agents are added/removed

2. **JSON-RPC Routing** (`/a2a`)
   - Uses agent card metadata for skill routing
   - Validates capabilities before processing requests
   - Supports multi-agent orchestration

## Benefits

### 1. **Persistence**
- Agent cards survive server restarts
- Can be version-controlled in Git
- Easy backup and disaster recovery

### 2. **Flexibility**
- Add agents without code changes
- Frontend can dynamically register agents
- Support for custom agent configurations

### 3. **Discoverability**
- All agents automatically available via A2A protocol
- Combined agent card shows entire system capabilities
- Standard REST API for agent management

### 4. **Maintainability**
- Human-readable JSON files
- Clear separation of concerns
- Easy to debug and audit

### 5. **Scalability**
- File-based storage is simple and fast
- Can migrate to database if needed
- Supports distributed agent systems

## Migration Path

### Current: Hardcoded Agent Cards
```python
# Old approach in server.py
def generate_agent_card(base_url: str) -> AgentCard:
    return AgentCard(
        name="Support Triage Agent",
        # ... hardcoded values
    )
```

### New: File-Based Storage
```python
# New approach
def generate_agent_card(base_url: str) -> AgentCard:
    store = get_agent_card_store()
    return store.get_combined_agent_card(base_url)
```

## Best Practices

### 1. **Unique Agent IDs**
- Use lowercase with hyphens: `support-triage`, `ops-assistant`
- Keep IDs stable (don't change once deployed)
- Use meaningful, descriptive names

### 2. **Skill Definitions**
- Provide clear descriptions
- Include relevant tags for discovery
- Add 3-5 example queries
- Keep skill IDs namespaced: `{agent-id}-{skill-name}`

### 3. **Versioning**
- Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
- Update version when changing capabilities
- Document breaking changes in description

### 4. **Metadata**
- Add custom metadata for tracking
- Include creation timestamps
- Tag source (frontend, default, migration)

### 5. **Validation**
- Use the AgentCard Pydantic model for validation
- Test agent cards with A2A protocol compliance tools
- Validate JSON schema before deployment

## Testing

### Test Agent Card Storage

```python
import pytest
from src.a2a.agent_cards import get_agent_card_store

def test_agent_card_crud():
    store = get_agent_card_store()
    
    # Create
    success = store.create_agent_from_config(
        agent_id="test-agent",
        name="Test Agent",
        description="Test",
        skills=[{
            "id": "test-skill",
            "name": "Test",
            "description": "Test",
            "tags": ["test"],
            "examples": []
        }],
        base_url="http://test"
    )
    assert success
    
    # Read
    card = store.get_agent_card("test-agent")
    assert card is not None
    assert card.name == "Test Agent"
    
    # Update
    card.description = "Updated"
    store.save_agent_card("test-agent", card)
    
    updated = store.get_agent_card("test-agent")
    assert updated.description == "Updated"
    
    # Delete
    deleted = store.delete_agent_card("test-agent")
    assert deleted
    
    not_found = store.get_agent_card("test-agent")
    assert not_found is None
```

### Test API Endpoints

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_agent_card_api():
    response = client.post("/api/agent-cards/", json={
        "agent_id": "api-test",
        "name": "API Test",
        "description": "Test via API",
        "base_url": "http://test",
        "skills": [{
            "id": "test",
            "name": "Test",
            "description": "Test",
            "tags": [],
            "examples": []
        }]
    })
    assert response.status_code == 201
    
    # Cleanup
    client.delete("/api/agent-cards/api-test")
```

## Future Enhancements

1. **Database Backend**
   - Option to use Cosmos DB instead of files
   - Better for high-concurrency scenarios
   - Maintains same API interface

2. **Agent Validation**
   - Validate agent implementations exist
   - Check skills match agent capabilities
   - Automated testing of agent endpoints

3. **Version Management**
   - Track agent card history
   - Rollback to previous versions
   - Migration tools for upgrades

4. **Discovery Service**
   - Central registry for distributed agents
   - Cross-system agent discovery
   - Federation support

5. **Access Control**
   - Authentication for agent card modifications
   - Role-based access control
   - Audit logging

## Troubleshooting

### Agent Card Not Found

**Problem:** `GET /.well-known/agent.json` returns empty or error

**Solution:**
1. Check if agent card files exist in `backend/data/agent-cards/`
2. Verify file permissions
3. Check application logs for storage errors
4. Ensure agent IDs are correct (lowercase, no spaces)

### Agent Not Showing in Combined Card

**Problem:** New agent doesn't appear in combined agent card

**Solution:**
1. Verify agent card file is valid JSON
2. Check the agent card conforms to A2A schema
3. Restart server to reload agent cards
4. Use `/api/agent-cards/` to list registered agents

### API Returns 500 Error

**Problem:** Agent card API operations fail with 500 error

**Solution:**
1. Check application logs for detailed error
2. Verify storage directory exists and is writable
3. Validate request payload matches API schema
4. Ensure agent IDs don't contain invalid characters

## Summary

The Agent Card Storage System provides a robust, flexible foundation for managing agent metadata in the Multi-Agent Demo. It seamlessly integrates with the A2A protocol while providing modern REST APIs for dynamic agent registration from the frontend. The file-based storage is simple, maintainable, and ready for production use.
