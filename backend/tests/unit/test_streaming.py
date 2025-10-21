"""
Unit tests for SSE streaming utilities.
"""

import pytest
import asyncio
import json
from datetime import datetime

from src.api.streaming import (
    StreamEvent,
    TokenEvent,
    TraceStartEvent,
    TraceUpdateEvent,
    TraceEndEvent,
    DoneEvent,
    ErrorEvent,
    HeartbeatEvent,
    EventGenerator
)


class TestStreamEvent:
    """Tests for StreamEvent base class."""
    
    def test_token_event_creation(self):
        """Test creating a TokenEvent."""
        event = TokenEvent(content="Hello")
        assert event.type == "token"
        assert event.content == "Hello"
        assert event.timestamp is not None
    
    def test_token_event_to_sse(self):
        """Test converting TokenEvent to SSE format."""
        event = TokenEvent(content="Hello")
        sse = event.to_sse()
        
        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")
        
        # Parse JSON
        json_str = sse[6:-2]  # Remove "data: " and "\n\n"
        data = json.loads(json_str)
        
        assert data["type"] == "token"
        assert data["content"] == "Hello"
        assert "timestamp" in data
    
    def test_trace_start_event(self):
        """Test creating TraceStartEvent."""
        event = TraceStartEvent(
            step_id="step_123",
            tool_name="test_tool",
            tool_type="mcp",
            input={"query": "test"},
            mcp_server="test-server"
        )
        
        assert event.type == "trace_start"
        assert event.step_id == "step_123"
        assert event.tool_name == "test_tool"
        assert event.tool_type == "mcp"
        assert event.input == {"query": "test"}
        assert event.mcp_server == "test-server"
    
    def test_trace_end_event(self):
        """Test creating TraceEndEvent."""
        event = TraceEndEvent(
            step_id="step_123",
            status="completed",
            output={"result": "success"},
            latency_ms=250
        )
        
        assert event.type == "trace_end"
        assert event.step_id == "step_123"
        assert event.status == "completed"
        assert event.output == {"result": "success"}
        assert event.latency_ms == 250
    
    def test_done_event(self):
        """Test creating DoneEvent."""
        event = DoneEvent(
            run_id="run_123",
            thread_id="thread_456",
            message_id="msg_789",
            tokens_used=150
        )
        
        assert event.type == "done"
        assert event.run_id == "run_123"
        assert event.thread_id == "thread_456"
        assert event.message_id == "msg_789"
        assert event.tokens_used == 150
    
    def test_error_event(self):
        """Test creating ErrorEvent."""
        event = ErrorEvent(
            error="Test error",
            details="Error details"
        )
        
        assert event.type == "error"
        assert event.error == "Test error"
        assert event.details == "Error details"
    
    def test_heartbeat_event(self):
        """Test creating HeartbeatEvent."""
        event = HeartbeatEvent()
        
        assert event.type == "heartbeat"


class TestEventGenerator:
    """Tests for EventGenerator class."""
    
    @pytest.mark.asyncio
    async def test_send_token(self):
        """Test sending token events."""
        gen = EventGenerator()
        
        await gen.send_token("Hello")
        await gen.send_token(" World")
        
        events = []
        async for event_str in gen.stream():
            events.append(event_str)
            if len(events) >= 2:
                break
        
        await gen.close()
        
        assert len(events) == 2
        assert "Hello" in events[0]
        assert "World" in events[1]
    
    @pytest.mark.asyncio
    async def test_send_trace_start(self):
        """Test sending trace start event."""
        gen = EventGenerator()
        
        await gen.send_trace_start(
            step_id="step_123",
            tool_name="test_tool",
            tool_type="mcp",
            input_data={"query": "test"}
        )
        
        events = []
        async for event_str in gen.stream():
            events.append(event_str)
            break
        
        await gen.close()
        
        assert len(events) == 1
        assert "trace_start" in events[0]
        assert "step_123" in events[0]
    
    @pytest.mark.asyncio
    async def test_send_trace_end(self):
        """Test sending trace end event."""
        gen = EventGenerator()
        
        await gen.send_trace_end(
            step_id="step_123",
            status="completed",
            output={"result": "success"},
            latency_ms=250
        )
        
        events = []
        async for event_str in gen.stream():
            events.append(event_str)
            break
        
        await gen.close()
        
        assert len(events) == 1
        assert "trace_end" in events[0]
        assert "completed" in events[0]
    
    @pytest.mark.asyncio
    async def test_send_done(self):
        """Test sending done event."""
        gen = EventGenerator()
        
        await gen.send_done(
            run_id="run_123",
            thread_id="thread_456",
            message_id="msg_789",
            tokens_used=150
        )
        
        events = []
        async for event_str in gen.stream():
            events.append(event_str)
            break
        
        await gen.close()
        
        assert len(events) == 1
        assert "done" in events[0]
        assert "run_123" in events[0]
    
    @pytest.mark.asyncio
    async def test_send_error(self):
        """Test sending error event."""
        gen = EventGenerator()
        
        await gen.send_error(error="Test error", details="Error details")
        
        events = []
        async for event_str in gen.stream():
            events.append(event_str)
            break
        
        await gen.close()
        
        assert len(events) == 1
        assert "error" in events[0]
        assert "Test error" in events[0]
    
    @pytest.mark.asyncio
    async def test_multiple_events(self):
        """Test sending multiple events."""
        gen = EventGenerator()
        
        await gen.send_token("Hello")
        await gen.send_token(" ")
        await gen.send_token("World")
        await gen.send_done("run_123", "thread_456", "msg_789", 100)
        
        events = []
        async for event_str in gen.stream():
            events.append(event_str)
            if len(events) >= 4:
                break
        
        await gen.close()
        
        assert len(events) == 4
        assert all("data: " in e for e in events)
    
    @pytest.mark.asyncio
    async def test_heartbeat(self):
        """Test heartbeat generation."""
        gen = EventGenerator(heartbeat_interval=0.1)  # 100ms for testing
        
        # Start heartbeat
        await gen.start_heartbeat()
        
        # Wait for a heartbeat
        await asyncio.sleep(0.15)
        
        # Get events
        events = []
        try:
            async for event_str in gen.stream():
                events.append(event_str)
                if len(events) >= 1:
                    break
        except asyncio.TimeoutError:
            pass
        
        await gen.close()
        
        # Should have received at least one heartbeat
        assert len(events) >= 1
        assert any("heartbeat" in e for e in events)
    
    @pytest.mark.asyncio
    async def test_sse_format(self):
        """Test SSE format compliance."""
        gen = EventGenerator()
        
        await gen.send_token("Test")
        
        events = []
        async for event_str in gen.stream():
            events.append(event_str)
            break
        
        await gen.close()
        
        # Check SSE format
        assert events[0].startswith("data: ")
        assert events[0].endswith("\n\n")
        
        # Parse JSON
        json_str = events[0][6:-2]
        data = json.loads(json_str)
        assert "type" in data
        assert "timestamp" in data
