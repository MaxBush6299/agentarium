"""
SSE Streaming Utilities
Server-Sent Events (SSE) streaming for real-time chat responses.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncIterator, Dict, Any, Optional, Literal
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# SSE Event Models
class StreamEvent(BaseModel):
    """Base class for SSE stream events."""
    type: str
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)
    
    def to_sse(self) -> str:
        """Convert event to SSE format."""
        data = self.model_dump_json()
        return f"data: {data}\n\n"
    
    class Config:
        # Allow subclasses to override type with Literal
        validate_assignment = False


class TokenEvent(StreamEvent):
    """Token event - a chunk of the assistant's response."""
    type: str = "token"
    content: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "token",
                "content": "To create a storage account",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }


class TraceStartEvent(StreamEvent):
    """Trace start event - tool call initiated."""
    type: str = "trace_start"
    step_id: str
    tool_name: str
    tool_type: str
    input: Dict[str, Any]
    
    # Optional tool-specific metadata
    mcp_server: Optional[str] = None
    openapi_endpoint: Optional[str] = None
    a2a_agent: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "trace_start",
                "step_id": "step_123",
                "tool_name": "microsoft_learn_search",
                "tool_type": "mcp",
                "input": {"query": "create storage account"},
                "mcp_server": "microsoft-learn",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }


class TraceUpdateEvent(StreamEvent):
    """Trace update event - tool call progress update."""
    type: str = "trace_update"
    step_id: str
    status: str
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "trace_update",
                "step_id": "step_123",
                "status": "in_progress",
                "message": "Searching Microsoft Learn...",
                "timestamp": "2025-01-15T10:30:01Z"
            }
        }


class TraceEndEvent(StreamEvent):
    """Trace end event - tool call completed."""
    type: str = "trace_end"
    step_id: str
    status: str  # "completed" or "failed"
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None
    
    # Token usage if applicable
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tokens_total: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "trace_end",
                "step_id": "step_123",
                "status": "completed",
                "output": {"results": [{"title": "Create storage account", "url": "..."}]},
                "latency_ms": 2000,
                "timestamp": "2025-01-15T10:30:02Z"
            }
        }


class DoneEvent(StreamEvent):
    """Done event - response completed."""
    type: str = "done"
    run_id: str
    thread_id: str
    message_id: str
    tokens_used: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "done",
                "run_id": "run_456",
                "thread_id": "thread_789",
                "message_id": "msg_124",
                "tokens_used": 1500,
                "timestamp": "2025-01-15T10:30:10Z"
            }
        }


class ErrorEvent(StreamEvent):
    """Error event - an error occurred."""
    type: str = "error"
    error: str
    details: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "error": "Tool call failed",
                "details": "Connection timeout to MCP server",
                "timestamp": "2025-01-15T10:30:05Z"
            }
        }


class HeartbeatEvent(StreamEvent):
    """Heartbeat event - keep connection alive."""
    type: str = "heartbeat"
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "heartbeat",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }


class EventGenerator:
    """
    Async generator for SSE events with buffering and heartbeat.
    """
    
    def __init__(
        self,
        heartbeat_interval: float = 15.0,
        buffer_size: int = 10,
        flush_interval: float = 0.1
    ):
        """
        Initialize event generator.
        
        Args:
            heartbeat_interval: Seconds between heartbeat events
            buffer_size: Number of events to buffer before flushing
            flush_interval: Seconds to wait before flushing buffer
        """
        self.heartbeat_interval = heartbeat_interval
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        self.queue: asyncio.Queue = asyncio.Queue()
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.closed = False
    
    async def start_heartbeat(self):
        """Start heartbeat task to keep connection alive."""
        async def heartbeat_loop():
            try:
                while not self.closed:
                    await asyncio.sleep(self.heartbeat_interval)
                    if not self.closed:
                        await self.queue.put(HeartbeatEvent())
            except asyncio.CancelledError:
                pass
        
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def send(self, event: StreamEvent):
        """
        Send an event to the stream.
        
        Args:
            event: Event to send
        """
        if not self.closed:
            await self.queue.put(event)
    
    async def send_token(self, content: str):
        """Send a token event."""
        await self.send(TokenEvent(content=content))
    
    async def send_trace_start(
        self,
        step_id: str,
        tool_name: str,
        tool_type: str,
        input_data: Dict[str, Any],
        **kwargs
    ):
        """Send a trace start event."""
        await self.send(TraceStartEvent(
            step_id=step_id,
            tool_name=tool_name,
            tool_type=tool_type,
            input=input_data,
            **kwargs
        ))
    
    async def send_trace_update(self, step_id: str, status: str, message: Optional[str] = None):
        """Send a trace update event."""
        await self.send(TraceUpdateEvent(
            step_id=step_id,
            status=status,
            message=message
        ))
    
    async def send_trace_end(
        self,
        step_id: str,
        status: str,  # "completed" or "failed"
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        latency_ms: Optional[int] = None,
        **kwargs
    ):
        """Send a trace end event."""
        await self.send(TraceEndEvent(
            step_id=step_id,
            status=status,
            output=output,
            error=error,
            latency_ms=latency_ms,
            **kwargs
        ))
    
    async def send_done(
        self,
        run_id: str,
        thread_id: str,
        message_id: str,
        tokens_used: int
    ):
        """Send a done event."""
        await self.send(DoneEvent(
            run_id=run_id,
            thread_id=thread_id,
            message_id=message_id,
            tokens_used=tokens_used
        ))
    
    async def send_error(self, error: str, details: Optional[str] = None):
        """Send an error event."""
        await self.send(ErrorEvent(error=error, details=details))
    
    async def close(self):
        """Close the event stream."""
        self.closed = True
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
    
    async def stream(self) -> AsyncIterator[str]:
        """
        Stream SSE events as formatted strings.
        
        Yields:
            SSE-formatted event strings
        """
        # Start heartbeat
        await self.start_heartbeat()
        
        try:
            buffer = []
            last_flush = asyncio.get_event_loop().time()
            
            while not self.closed or not self.queue.empty():
                try:
                    # Wait for event with timeout to allow periodic flushing
                    event = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=self.flush_interval
                    )
                    buffer.append(event)
                    
                    # Flush if buffer is full
                    if len(buffer) >= self.buffer_size:
                        for evt in buffer:
                            yield evt.to_sse()
                        buffer = []
                        last_flush = asyncio.get_event_loop().time()
                    
                except asyncio.TimeoutError:
                    # Flush buffer on timeout
                    if buffer:
                        current_time = asyncio.get_event_loop().time()
                        if current_time - last_flush >= self.flush_interval:
                            for evt in buffer:
                                yield evt.to_sse()
                            buffer = []
                            last_flush = current_time
            
            # Flush remaining events
            for evt in buffer:
                yield evt.to_sse()
        
        finally:
            await self.close()


def format_sse_event(event: StreamEvent) -> str:
    """
    Format an event as SSE.
    
    Args:
        event: Event to format
        
    Returns:
        SSE-formatted string
    """
    return event.to_sse()


async def send_sse_error(error_message: str, details: Optional[str] = None) -> str:
    """
    Create an SSE-formatted error event.
    
    Args:
        error_message: Error message
        details: Optional error details
        
    Returns:
        SSE-formatted error event
    """
    event = ErrorEvent(error=error_message, details=details)
    return event.to_sse()
