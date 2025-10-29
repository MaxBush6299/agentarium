"""
Persistence Models for Chat Conversations
Pydantic models for Thread, Run, Step, Message, and ToolCall entities.
Maps to Cosmos DB collections with proper validation and serialization.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


# Enums for status tracking
class RunStatus(str, Enum):
    """Status of an agent run."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Status of a step/trace."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StepType(str, Enum):
    """Type of step in the execution."""
    TOOL_CALL = "tool_call"
    MESSAGE = "message"
    ERROR = "error"


# Core Models
class Message(BaseModel):
    """
    A message in a conversation thread.
    Can be from user, assistant, or system.
    """
    id: str = Field(description="Unique message ID")
    role: Literal["user", "assistant", "system"] = Field(description="Message sender role")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_123",
                "role": "user",
                "content": "How do I create a storage account?",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }


class ToolCall(BaseModel):
    """
    A tool call made during agent execution.
    Represents a single function/tool invocation.
    """
    id: str = Field(description="Unique tool call ID")
    tool_name: str = Field(description="Name of the tool/function called")
    tool_type: Literal["mcp", "openapi", "a2a", "builtin"] = Field(description="Type of tool")
    input: Dict[str, Any] = Field(description="Tool input parameters")
    output: Optional[Dict[str, Any]] = Field(default=None, description="Tool output/result")
    status: StepStatus = Field(default=StepStatus.IN_PROGRESS, description="Tool call status")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Tool call start time")
    completed_at: Optional[datetime] = Field(default=None, description="Tool call completion time")
    latency_ms: Optional[int] = Field(default=None, description="Tool call latency in milliseconds")
    
    # Tool-specific metadata
    mcp_server: Optional[str] = Field(default=None, description="MCP server name if MCP tool")
    openapi_endpoint: Optional[str] = Field(default=None, description="OpenAPI endpoint if OpenAPI tool")
    a2a_agent: Optional[str] = Field(default=None, description="A2A agent name if A2A tool")
    
    # Token usage (if applicable)
    tokens_input: Optional[int] = Field(default=None, description="Input tokens used")
    tokens_output: Optional[int] = Field(default=None, description="Output tokens used")
    tokens_total: Optional[int] = Field(default=None, description="Total tokens used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "call_123",
                "tool_name": "microsoft_learn_search",
                "tool_type": "mcp",
                "input": {"query": "create storage account"},
                "output": {"results": [{"title": "Create storage account", "url": "..."}]},
                "status": "completed",
                "started_at": "2025-01-15T10:30:00Z",
                "completed_at": "2025-01-15T10:30:02Z",
                "latency_ms": 2000,
                "mcp_server": "microsoft-learn"
            }
        }


class Step(BaseModel):
    """
    A step in an agent run execution.
    Represents a single action (tool call, message generation, etc.).
    """
    id: str = Field(alias="stepId", description="Unique step ID")
    run_id: str = Field(description="Parent run ID")
    thread_id: str = Field(description="Parent thread ID")
    agent_id: str = Field(description="Agent ID executing this step")
    
    step_type: StepType = Field(description="Type of step")
    status: StepStatus = Field(default=StepStatus.IN_PROGRESS, description="Step status")
    
    # Step details
    tool_call: Optional[ToolCall] = Field(default=None, description="Tool call details if step_type=tool_call")
    message: Optional[Message] = Field(default=None, description="Message details if step_type=message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Step start time")
    completed_at: Optional[datetime] = Field(default=None, description="Step completion time")
    
    # Cosmos DB fields
    etag: Optional[str] = Field(default=None, description="Cosmos DB etag for optimistic concurrency")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "step_123",
                "run_id": "run_456",
                "thread_id": "thread_789",
                "agent_id": "support-triage",
                "step_type": "tool_call",
                "status": "completed",
                "tool_call": {
                    "id": "call_123",
                    "tool_name": "microsoft_learn_search",
                    "tool_type": "mcp",
                    "input": {"query": "create storage account"},
                    "status": "completed"
                }
            }
        }


class Run(BaseModel):
    """
    An agent run represents a single execution cycle.
    Triggered by a user message and produces an assistant response.
    """
    id: str = Field(description="Unique run ID")
    thread_id: str = Field(alias="threadId", description="Parent thread ID")
    agent_id: str = Field(description="Agent ID executing this run")
    
    status: RunStatus = Field(default=RunStatus.QUEUED, description="Run status")
    
    # Model configuration
    model: str = Field(description="Model used for this run (e.g., gpt-4o)")
    temperature: Optional[float] = Field(default=0.7, description="Model temperature")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens for response")
    
    # User message that triggered this run
    user_message_id: str = Field(description="ID of the user message that triggered this run")
    
    # Assistant response
    assistant_message_id: Optional[str] = Field(default=None, description="ID of the assistant response message")
    
    # Execution metadata
    steps: List[str] = Field(default_factory=list, description="List of step IDs in execution order")
    error: Optional[str] = Field(default=None, description="Error message if run failed")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Run creation time")
    started_at: Optional[datetime] = Field(default=None, description="Run start time")
    completed_at: Optional[datetime] = Field(default=None, description="Run completion time")
    
    # Token usage
    tokens_input: int = Field(default=0, description="Total input tokens")
    tokens_output: int = Field(default=0, description="Total output tokens")
    tokens_total: int = Field(default=0, description="Total tokens")
    
    # Cost tracking
    cost_usd: Optional[float] = Field(default=None, description="Estimated cost in USD")
    
    # Cosmos DB fields
    etag: Optional[str] = Field(default=None, description="Cosmos DB etag")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "run_456",
                "thread_id": "thread_789",
                "agent_id": "support-triage",
                "status": "completed",
                "model": "gpt-4o",
                "user_message_id": "msg_123",
                "assistant_message_id": "msg_124",
                "steps": ["step_1", "step_2"],
                "tokens_total": 1500,
                "created_at": "2025-01-15T10:30:00Z"
            }
        }


class Thread(BaseModel):
    """
    A conversation thread between a user and an agent.
    Contains message history and run history.
    """
    id: str = Field(description="Unique thread ID")
    agent_id: str = Field(alias="agentId", description="Agent ID for this thread")
    
    # Thread metadata
    title: Optional[str] = Field(default=None, description="Thread title (auto-generated from first message)")
    user_id: Optional[str] = Field(default=None, description="User ID who created this thread")
    
    # Conversation history
    messages: List[Message] = Field(default_factory=list, description="List of messages in chronological order")
    
    # Run history
    runs: List[str] = Field(default_factory=list, description="List of run IDs in chronological order")
    
    # Status
    status: Literal["active", "archived", "deleted"] = Field(default="active", description="Thread status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thread creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    # Cosmos DB fields
    etag: Optional[str] = Field(default=None, description="Cosmos DB etag")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "thread_789",
                "agent_id": "support-triage",
                "title": "How to create Azure storage account",
                "user_id": "user_123",
                "messages": [
                    {
                        "id": "msg_123",
                        "role": "user",
                        "content": "How do I create a storage account?",
                        "timestamp": "2025-01-15T10:30:00Z"
                    }
                ],
                "runs": ["run_456"],
                "status": "active",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }


# Request/Response Models for API
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(description="User message content", min_length=1, max_length=10000)
    thread_id: Optional[str] = Field(default=None, description="Existing thread ID (optional, creates new if not provided)")
    stream: bool = Field(default=True, description="Enable SSE streaming")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "How do I create a storage account in Azure?",
                "thread_id": "thread_789",
                "stream": True
            }
        }


class ChatResponse(BaseModel):
    """Response model for non-streaming chat."""
    thread_id: str = Field(description="Thread ID")
    run_id: str = Field(description="Run ID")
    message: Message = Field(description="Assistant response message")
    tokens_used: int = Field(description="Total tokens used")


class ThreadListResponse(BaseModel):
    """Response model for listing threads."""
    threads: List[Thread] = Field(description="List of threads")
    total: int = Field(description="Total number of threads")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=50, description="Page size")


# ============================================================================
# Agent Management Models (Phase 2.12)
# ============================================================================

class AgentStatus(str, Enum):
    """Status of an agent."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class ToolType(str, Enum):
    """Type of tool available to agents."""
    MCP = "mcp"
    OPENAPI = "openapi"
    A2A = "a2a"
    BUILTIN = "builtin"


class ToolConfig(BaseModel):
    """Configuration for an agent tool."""
    type: ToolType = Field(description="Type of tool")
    name: str = Field(description="Tool name/identifier")
    
    # Type-specific configuration
    mcp_server_name: Optional[str] = Field(default=None, description="MCP server name")
    openapi_spec_path: Optional[str] = Field(default=None, description="Path to OpenAPI spec file")
    a2a_agent_id: Optional[str] = Field(default=None, description="A2A agent identifier")
    
    # Additional config
    config: Optional[Dict[str, Any]] = Field(default=None, description="Tool-specific configuration")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "mcp",
                "name": "microsoft-docs",
                "mcp_server_name": "microsoft-learn-mcp",
                "enabled": True
            }
        }


class AgentMetadata(BaseModel):
    """
    Metadata for an agent in the registry.
    Stored in Cosmos DB 'agents' collection.
    """
    id: str = Field(description="Unique agent ID (e.g., 'support-triage')")
    name: str = Field(description="Display name")
    description: str = Field(description="Agent description")
    system_prompt: str = Field(description="System prompt/instructions")
    
    # Model configuration
    model: str = Field(default="gpt-4o", description="Azure OpenAI model name")
    temperature: float = Field(default=0.7, description="Temperature setting")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens per response")
    max_messages: int = Field(default=20, description="Sliding window size")
    
    # Tools configuration
    tools: List[ToolConfig] = Field(default_factory=list, description="List of tools")
    
    # Capabilities
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    
    # Status and visibility
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="Agent status")
    is_public: bool = Field(default=True, description="Whether agent is visible to all users")
    coordinator_only: bool = Field(default=False, description="If True, agent is only available as workflow coordinator, not for direct chat")
    
    # Metadata
    created_by: str = Field(default="system", description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    version: str = Field(default="1.0.0", description="Agent version")
    
    # Usage statistics
    total_runs: int = Field(default=0, description="Total number of runs")
    total_tokens: int = Field(default=0, description="Total tokens used")
    avg_latency_ms: Optional[float] = Field(default=None, description="Average response latency")
    last_used_at: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    
    # Cosmos DB fields
    etag: Optional[str] = Field(default=None, description="Cosmos DB etag")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "support-triage",
                "name": "Support Triage Agent",
                "description": "Helps triage customer support issues using Microsoft documentation",
                "system_prompt": "You are a support specialist...",
                "model": "gpt-4o",
                "temperature": 0.7,
                "tools": [
                    {
                        "type": "mcp",
                        "name": "microsoft-docs",
                        "mcp_server_name": "microsoft-learn-mcp"
                    }
                ],
                "capabilities": ["documentation_search", "issue_triage"],
                "status": "active",
                "version": "1.0.0"
            }
        }


class AgentCreateRequest(BaseModel):
    """Request model for creating a new agent."""
    id: str
    name: str
    description: str
    system_prompt: str
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    max_messages: int = 20
    tools: List[ToolConfig] = []
    capabilities: List[str] = []
    is_public: bool = True


class AgentUpdateRequest(BaseModel):
    """Request model for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    max_messages: Optional[int] = None
    tools: Optional[List[ToolConfig]] = None
    capabilities: Optional[List[str]] = None
    is_public: Optional[bool] = None
    status: Optional[AgentStatus] = None


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    agents: List[AgentMetadata] = Field(description="List of agents")
    total: int = Field(description="Total number of agents")
    limit: int = Field(default=50, description="Page size")
    offset: int = Field(default=0, description="Offset")

