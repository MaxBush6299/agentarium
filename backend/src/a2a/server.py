"""
A2A (Agent-to-Agent) Protocol Server Implementation

Implements the A2A Protocol specification (https://a2a-protocol.org/latest/specification/)
for the Support Triage Agent to enable agent-to-agent communication.

This module provides:
- Agent Card generation at /.well-known/agent.json
- JSON-RPC 2.0 endpoint for A2A protocol messages
- Task management for message/send, tasks/get, tasks/cancel methods
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..agents.support_triage import SupportTriageAgent
from ..config import get_settings
from .agent_cards import (
    get_agent_card_store,
    AgentCard as StoredAgentCard,
    AgentSkill as StoredAgentSkill,
    AgentCapabilities as StoredAgentCapabilities
)

logger = logging.getLogger(__name__)


# ============================================================================
# A2A Protocol Data Models (based on specification Section 6)
# ============================================================================

class TaskState(str, Enum):
    """Task lifecycle states per A2A spec Section 6.3"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    REJECTED = "rejected"
    AUTH_REQUIRED = "auth-required"
    UNKNOWN = "unknown"


class TextPart(BaseModel):
    """Text content part per A2A spec Section 6.5.1"""
    kind: str = "text"
    text: str


class DataPart(BaseModel):
    """Structured data part per A2A spec Section 6.5.3"""
    kind: str = "data"
    data: Dict[str, Any]


class Message(BaseModel):
    """A2A Message object per spec Section 6.4"""
    role: str  # "user" or "agent"
    parts: List[Any]  # List of TextPart, FilePart, or DataPart
    messageId: str
    taskId: Optional[str] = None
    contextId: Optional[str] = None
    kind: str = "message"
    metadata: Optional[Dict[str, Any]] = None


class TaskStatus(BaseModel):
    """Task status per A2A spec Section 6.2"""
    state: TaskState
    message: Optional[Message] = None
    timestamp: Optional[str] = None


class Artifact(BaseModel):
    """Task artifact per A2A spec Section 6.7"""
    artifactId: str
    name: Optional[str] = None
    description: Optional[str] = None
    parts: List[Any]  # List of TextPart, FilePart, or DataPart
    metadata: Optional[Dict[str, Any]] = None


class Task(BaseModel):
    """A2A Task object per spec Section 6.1"""
    id: str
    contextId: str
    status: TaskStatus
    history: Optional[List[Message]] = None
    artifacts: Optional[List[Artifact]] = None
    kind: str = "task"
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# JSON-RPC 2.0 Protocol Models (based on specification Section 6.11)
# ============================================================================

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request per A2A spec Section 6.11.1"""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 Error per A2A spec Section 6.12"""
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response per A2A spec Section 6.11.2"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


# ============================================================================
# Agent Card Models (based on specification Section 5)
# ============================================================================

class AgentProvider(BaseModel):
    """Agent provider information per A2A spec Section 5.5.1"""
    organization: str
    url: str


class AgentCapabilities(BaseModel):
    """Agent capabilities per A2A spec Section 5.5.2"""
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class AgentSkill(BaseModel):
    """Agent skill definition per A2A spec Section 5.5.4"""
    id: str
    name: str
    description: str
    tags: List[str]
    examples: Optional[List[str]] = None
    inputModes: Optional[List[str]] = None
    outputModes: Optional[List[str]] = None


class AgentCard(BaseModel):
    """
    Agent Card per A2A Protocol Specification Section 5.5
    
    The Agent Card is a JSON metadata document that describes the agent's:
    - Identity (name, description, version)
    - Capabilities (streaming, push notifications)
    - Skills (what the agent can do)
    - Service endpoints and authentication requirements
    """
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    url: str
    preferredTransport: str = "JSONRPC"
    provider: Optional[AgentProvider] = None
    iconUrl: Optional[str] = None
    version: str
    documentationUrl: Optional[str] = None
    capabilities: AgentCapabilities
    defaultInputModes: List[str] = ["application/json", "text/plain"]
    defaultOutputModes: List[str] = ["application/json", "text/plain"]
    skills: List[AgentSkill]
    supportsAuthenticatedExtendedCard: bool = False


# ============================================================================
# In-Memory Task Storage
# ============================================================================

class TaskStore:
    """
    Simple in-memory task storage.
    In production, this would be replaced with persistent storage (Cosmos DB, etc.)
    """
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.contexts: Dict[str, List[str]] = {}  # contextId -> [taskIds]
    
    def create_task(self, context_id: str, initial_message: Message) -> Task:
        """Create a new task with initial message"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp=datetime.utcnow().isoformat() + "Z"
            ),
            history=[initial_message],
            artifacts=[],
            metadata={}
        )
        self.tasks[task_id] = task
        
        if context_id not in self.contexts:
            self.contexts[context_id] = []
        self.contexts[context_id].append(task_id)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID"""
        return self.tasks.get(task_id)
    
    def update_task(self, task: Task):
        """Update an existing task"""
        self.tasks[task.id] = task
    
    def cancel_task(self, task_id: str) -> Optional[Task]:
        """Cancel a task if it's in a cancelable state"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        # Check if task can be canceled
        if task.status.state in [TaskState.COMPLETED, TaskState.CANCELED, TaskState.FAILED, TaskState.REJECTED]:
            return None
        
        task.status.state = TaskState.CANCELED
        task.status.timestamp = datetime.utcnow().isoformat() + "Z"
        return task


# Global task store instance
task_store = TaskStore()


# ============================================================================
# Agent Card Generation
# ============================================================================

def generate_agent_card(base_url: str) -> AgentCard:
    """
    Generate the combined Agent Card from file-based storage.
    
    Per A2A spec Section 5, the Agent Card describes the agent's identity,
    capabilities, and available skills for discovery by other agents.
    
    This function reads all agent cards from the file-based store and
    returns a combined card listing all available agents as skills.
    
    Args:
        base_url: The base URL where the agent is hosted (e.g., http://localhost:8000)
    
    Returns:
        AgentCard object representing all registered agents
    """
    try:
        # Get the agent card store
        store = get_agent_card_store()
        
        # Get combined agent card from all stored cards
        stored_card = store.get_combined_agent_card(base_url)
        
        # Convert stored card model to server AgentCard model
        # Map the stored capabilities and skills to the server models
        capabilities = AgentCapabilities(
            streaming=stored_card.capabilities.streaming,
            pushNotifications=stored_card.capabilities.pushNotifications,
            stateTransitionHistory=stored_card.capabilities.stateTransitionHistory
        )
        
        skills = []
        for stored_skill in stored_card.skills:
            skill = AgentSkill(
                id=stored_skill.id,
                name=stored_skill.name,
                description=stored_skill.description,
                tags=stored_skill.tags,
                examples=stored_skill.examples
            )
            skills.append(skill)
        
        # Create the agent card
        agent_card = AgentCard(
            protocolVersion=stored_card.protocolVersion,
            name=stored_card.name,
            description=stored_card.description,
            url=stored_card.url,
            preferredTransport=stored_card.preferredTransport,
            version=stored_card.version,
            provider=AgentProvider(
                organization=stored_card.provider or "Multi-Agent Demo",
                url=base_url
            ),
            capabilities=capabilities,
            skills=skills,
            documentationUrl=f"{base_url}/docs"
        )
        
        return agent_card
        
    except Exception as e:
        logger.error(f"Failed to generate agent card from store: {e}")
        # Return a default fallback card
        return AgentCard(
            name="Multi-Agent System",
            description="Error loading agent cards",
            url=f"{base_url}/a2a",
            version="1.0.0",
            provider=AgentProvider(
                organization="Agent Demo Project",
                url=base_url
            ),
            capabilities=AgentCapabilities(
                streaming=False,
                pushNotifications=False,
                stateTransitionHistory=False
            ),
            skills=[],
            documentationUrl=f"{base_url}/docs"
        )


# ============================================================================
# A2A Message Handler
# ============================================================================

async def handle_message_send(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle message/send method per A2A spec Section 7.1
    
    This method sends a message to the agent to initiate a new interaction
    or continue an existing one. Returns the task state after processing.
    
    Args:
        params: MessageSendParams containing the message and optional configuration
    
    Returns:
        Task object with updated status
    """
    # Extract message from params
    message_data = params.get("message")
    if not message_data:
        raise ValueError("Missing 'message' in params")
    
    # Parse message
    message = Message(**message_data)
    
    # Get or create context ID
    context_id = message.contextId or str(uuid.uuid4())
    task_id = message.taskId
    
    # If taskId provided, continue existing task; otherwise create new
    if task_id:
        task = task_store.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Add message to history
        task.history.append(message)
        task.status.state = TaskState.WORKING
    else:
        # Create new task
        task = task_store.create_task(context_id, message)
    
    # Update task status to working
    task.status.state = TaskState.WORKING
    task.status.timestamp = datetime.utcnow().isoformat() + "Z"
    task_store.update_task(task)
    
    # Extract user message text
    user_text = ""
    for part in message.parts:
        if isinstance(part, dict) and part.get("kind") == "text":
            user_text = part.get("text", "")
        elif hasattr(part, "text"):
            user_text = part.text
    
    try:
        # Create Support Triage Agent and process message
        agent = await SupportTriageAgent.create()
        response = await agent.run(user_text)
        
        # Create response message
        response_message = Message(
            role="agent",
            parts=[TextPart(text=response.messages[-1].text)],
            messageId=str(uuid.uuid4()),
            taskId=task.id,
            contextId=context_id
        )
        
        # Add to task history
        task.history.append(response_message)
        
        # Create artifact with the response
        artifact = Artifact(
            artifactId=str(uuid.uuid4()),
            name="Support Triage Response",
            parts=[TextPart(text=response.messages[-1].text)]
        )
        task.artifacts.append(artifact)
        
        # Update task status to completed
        task.status.state = TaskState.COMPLETED
        task.status.message = response_message
        task.status.timestamp = datetime.utcnow().isoformat() + "Z"
        
    except Exception as e:
        # Handle errors
        error_message = Message(
            role="agent",
            parts=[TextPart(text=f"Error processing request: {str(e)}")],
            messageId=str(uuid.uuid4()),
            taskId=task.id,
            contextId=context_id
        )
        task.history.append(error_message)
        task.status.state = TaskState.FAILED
        task.status.message = error_message
        task.status.timestamp = datetime.utcnow().isoformat() + "Z"
    
    task_store.update_task(task)
    return task.model_dump()


async def handle_tasks_get(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle tasks/get method per A2A spec Section 7.3
    
    Retrieves the current state of a task by ID.
    
    Args:
        params: TaskQueryParams containing task ID and optional historyLength
    
    Returns:
        Task object
    """
    task_id = params.get("id")
    if not task_id:
        raise ValueError("Missing 'id' in params")
    
    task = task_store.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    # Optionally limit history length
    history_length = params.get("historyLength")
    if history_length is not None and task.history:
        task.history = task.history[-history_length:]
    
    return task.model_dump()


async def handle_tasks_cancel(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle tasks/cancel method per A2A spec Section 7.5
    
    Attempts to cancel an ongoing task.
    
    Args:
        params: TaskIdParams containing task ID
    
    Returns:
        Updated Task object
    """
    task_id = params.get("id")
    if not task_id:
        raise ValueError("Missing 'id' in params")
    
    task = task_store.cancel_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found or cannot be canceled")
    
    return task.model_dump()


# ============================================================================
# FastAPI Router Setup
# ============================================================================

# Router for A2A protocol endpoints
router = APIRouter(prefix="/a2a", tags=["A2A Protocol"])

# Router for well-known agent card (at root level per spec Section 5.3)
well_known_router = APIRouter(tags=["A2A Discovery"])


@well_known_router.get("/.well-known/agent.json", response_model=AgentCard)
async def get_agent_card(request: Request):
    """
    Serve the Agent Card at the well-known location per A2A spec Section 5.3
    
    For Python implementations, the recommended location is /.well-known/agent.json
    (C# implementations use /.well-known/agent-card.json)
    
    This endpoint must be at the domain root level, not under any prefix.
    """
    base_url = str(request.base_url).rstrip("/")
    return generate_agent_card(base_url)


@router.post("")
@router.post("/")
async def a2a_endpoint(request: Request):
    """
    A2A JSON-RPC 2.0 endpoint per A2A spec Section 3 and 7
    
    Handles JSON-RPC 2.0 requests for the A2A protocol, supporting:
    - message/send: Send messages to the agent
    - tasks/get: Retrieve task status
    - tasks/cancel: Cancel ongoing tasks
    
    Per spec Section 3.2.1, this endpoint:
    - Accepts JSON-RPC 2.0 requests over HTTP POST
    - Content-Type must be application/json
    - Returns JSON-RPC 2.0 responses
    """
    try:
        # Parse JSON-RPC request
        body = await request.json()
        rpc_request = JSONRPCRequest(**body)
        
        # Route to appropriate handler
        result = None
        error = None
        
        try:
            if rpc_request.method == "message/send":
                result = await handle_message_send(rpc_request.params or {})
            elif rpc_request.method == "tasks/get":
                result = await handle_tasks_get(rpc_request.params or {})
            elif rpc_request.method == "tasks/cancel":
                result = await handle_tasks_cancel(rpc_request.params or {})
            else:
                # Method not found error per spec Section 8.1
                error = JSONRPCError(
                    code=-32601,
                    message="Method not found",
                    data={"method": rpc_request.method}
                )
        except ValueError as e:
            # Invalid params error per spec Section 8.1
            error = JSONRPCError(
                code=-32602,
                message="Invalid params",
                data={"error": str(e)}
            )
        except Exception as e:
            # Internal error per spec Section 8.1
            error = JSONRPCError(
                code=-32603,
                message="Internal error",
                data={"error": str(e)}
            )
        
        # Build JSON-RPC response
        response = JSONRPCResponse(
            id=rpc_request.id,
            result=result,
            error=error
        )
        
        return JSONResponse(content=response.model_dump(exclude_none=True))
        
    except Exception as e:
        # Parse error per spec Section 8.1
        error_response = JSONRPCResponse(
            id=None,
            error=JSONRPCError(
                code=-32700,
                message="Parse error",
                data={"error": str(e)}
            )
        )
        return JSONResponse(
            content=error_response.model_dump(exclude_none=True),
            status_code=400
        )
