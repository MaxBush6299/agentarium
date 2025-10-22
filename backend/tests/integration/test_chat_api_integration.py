"""
Integration tests for Chat API endpoints.

These tests verify the full integration of:
- Chat API endpoints
- SSE streaming
- Persistence (Cosmos DB)
- Agent execution

Note: These tests require:
1. Backend server NOT running (httpx will connect to FastAPI app directly)
2. Cosmos DB configured and accessible
3. Azure OpenAI configured
4. Environment variables set (.env file)
"""

import pytest
import asyncio
import json
import httpx
from httpx import ASGITransport
from datetime import datetime

from src.main import app
from src.persistence.models import RunStatus


@pytest.fixture
async def client():
    """Create an async httpx client for testing."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
class TestChatAPIIntegration:
    """Integration tests for Chat API."""
    
    async def test_chat_streaming_support_triage(self, client):
        """Test streaming chat with support-triage agent."""
        # Send chat request
        response = await client.post(
            "/api/agents/support-triage/chat",
            json={
                "message": "How do I create a storage account in Azure?",
                "stream": True
            },
            timeout=60.0
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    async def test_chat_streaming_azure_ops(self, client):
        """Test streaming chat with Azure Ops agent."""
        # Send chat request
        response = await client.post(
            "/api/agents/ops-assistant/chat",
            json={
                "message": "List all storage accounts",
                "stream": True
            },
            timeout=60.0
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    async def test_chat_invalid_agent(self):
        """Test chat with invalid agent ID."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/agents/invalid-agent/chat",
                json={
                    "message": "Test message",
                    "stream": True
                }
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    async def test_list_threads(self):
        """Test listing threads for an agent."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/agents/support-triage/threads")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "threads" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            
            assert isinstance(data["threads"], list)
            assert isinstance(data["total"], int)
    
    async def test_list_threads_with_pagination(self):
        """Test listing threads with pagination."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/agents/support-triage/threads",
                params={"limit": 5, "offset": 0}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["limit"] == 5
            assert data["offset"] == 0
            assert len(data["threads"]) <= 5
    
    async def test_get_thread_details(self):
        """Test getting thread details."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # First create a thread by sending a message
            chat_response = await client.post(
                "/api/agents/support-triage/chat",
                json={
                    "message": "Test message for thread retrieval",
                    "stream": True
                },
                timeout=60.0
            )
            
            # Parse the done event to get thread_id
            thread_id = None
            async for line in chat_response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "done":
                            thread_id = event.get("thread_id")
                            break
                    except:
                        pass
            
            if thread_id:
                # Get thread details
                response = await client.get(
                    f"/api/agents/support-triage/threads/{thread_id}"
                )
                
                assert response.status_code == 200
                thread = response.json()
                
                assert thread["id"] == thread_id
                assert thread["agent_id"] == "support-triage"
                assert "messages" in thread
                assert len(thread["messages"]) >= 2  # User + assistant
    
    async def test_delete_thread_soft(self):
        """Test soft deleting a thread."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Create a thread
            chat_response = await client.post(
                "/api/agents/support-triage/chat",
                json={
                    "message": "Test message for deletion",
                    "stream": True
                },
                timeout=60.0
            )
            
            # Parse thread_id from done event
            thread_id = None
            async for line in chat_response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "done":
                            thread_id = event.get("thread_id")
                            break
                    except:
                        pass
            
            if thread_id:
                # Soft delete the thread
                response = await client.delete(
                    f"/api/agents/support-triage/threads/{thread_id}"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "deleted" in data["message"].lower()
                
                # Verify thread is marked as deleted
                get_response = await client.get(
                    f"/api/agents/support-triage/threads/{thread_id}"
                )
                
                # Should return 404 or show status as deleted
                if get_response.status_code == 200:
                    thread = get_response.json()
                    assert thread["status"] == "deleted"
    
    async def test_chat_with_thread_continuation(self):
        """Test continuing a conversation in existing thread."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # First message
            response1 = await client.post(
                "/api/agents/support-triage/chat",
                json={
                    "message": "What is Azure?",
                    "stream": True
                },
                timeout=60.0
            )
            
            # Get thread_id from first response
            thread_id = None
            async for line in response1.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "done":
                            thread_id = event.get("thread_id")
                            break
                    except:
                        pass
            
            assert thread_id is not None
            
            # Second message in same thread
            response2 = await client.post(
                "/api/agents/support-triage/chat",
                json={
                    "message": "Tell me more about storage",
                    "thread_id": thread_id,
                    "stream": True
                },
                timeout=60.0
            )
            
            # Verify it's the same thread
            thread_id2 = None
            async for line in response2.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "done":
                            thread_id2 = event.get("thread_id")
                            break
                    except:
                        pass
            
            assert thread_id == thread_id2
            
            # Verify thread has multiple messages
            thread_response = await client.get(
                f"/api/agents/support-triage/threads/{thread_id}"
            )
            
            thread = thread_response.json()
            assert len(thread["messages"]) >= 4  # 2 user + 2 assistant


@pytest.mark.asyncio
class TestChatAPISSEFormat:
    """Test SSE event format compliance."""
    
    async def test_sse_events_format(self):
        """Test that SSE events follow correct format."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/agents/support-triage/chat",
                json={
                    "message": "Test SSE format",
                    "stream": True
                },
                timeout=60.0
            )
            
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    events.append(line)
                    if len(events) >= 5:  # Get first few events
                        break
            
            # Verify each event
            for event_line in events:
                assert event_line.startswith("data: ")
                
                # Parse JSON
                json_str = event_line[6:]
                try:
                    event = json.loads(json_str)
                    
                    # All events should have type and timestamp
                    assert "type" in event
                    assert "timestamp" in event
                    
                    # Verify event type
                    assert event["type"] in [
                        "token", "trace_start", "trace_update", 
                        "trace_end", "done", "error", "heartbeat"
                    ]
                    
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in SSE event: {json_str}")
    
    async def test_token_events(self):
        """Test that token events contain content."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/agents/support-triage/chat",
                json={
                    "message": "Hello",
                    "stream": True
                },
                timeout=60.0
            )
            
            token_events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "token":
                            token_events.append(event)
                            if len(token_events) >= 3:
                                break
                    except:
                        pass
            
            # Verify token events have content
            for event in token_events:
                assert "content" in event
                assert isinstance(event["content"], str)
    
    async def test_done_event(self):
        """Test that done event contains required fields."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/agents/support-triage/chat",
                json={
                    "message": "Test done event",
                    "stream": True
                },
                timeout=60.0
            )
            
            done_event = None
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "done":
                            done_event = event
                            break
                    except:
                        pass
            
            assert done_event is not None
            assert "run_id" in done_event
            assert "thread_id" in done_event
            assert "message_id" in done_event
            assert "tokens_used" in done_event


@pytest.mark.asyncio
class TestChatAPIErrorHandling:
    """Test error handling in Chat API."""
    
    async def test_invalid_request_body(self):
        """Test chat with invalid request body."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/agents/support-triage/chat",
                json={"invalid": "field"}  # Missing 'message' field
            )
            
            assert response.status_code == 422  # Validation error
    
    async def test_empty_message(self):
        """Test chat with empty message."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/agents/support-triage/chat",
                json={"message": "", "stream": True}
            )
            
            # Should either reject or handle gracefully
            assert response.status_code in [400, 422]
    
    async def test_get_nonexistent_thread(self):
        """Test getting a non-existent thread."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/agents/support-triage/threads/nonexistent_thread_id"
            )
            
            assert response.status_code == 404
    
    async def test_delete_nonexistent_thread(self):
        """Test deleting a non-existent thread."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(
                "/api/agents/support-triage/threads/nonexistent_thread_id"
            )
            
            assert response.status_code == 404
