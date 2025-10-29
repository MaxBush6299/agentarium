"""
Workflow Request/Response Models

Pydantic models for multi-agent workflow interaction.

Models:
- WorkflowType: Enumeration of supported workflow patterns
- WorkflowRequest: User input for workflow execution
- WorkflowResponse: Final response with metadata
- WorkflowTraceMetadata: Detailed trace of workflow execution
- AgentInteraction: Single agent interaction in trace
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# Workflow Type Enumeration
# ============================================================================

class WorkflowType(str, Enum):
    """Enumeration of workflow execution patterns."""
    
    HANDOFF = "handoff"
    """Multi-agent routing with sequential handoffs (intelligent-handoff pattern)."""
    
    SEQUENTIAL = "sequential"
    """Linear agent pipeline (agent1 → agent2 → agent3 → ...). Output of each becomes input to next."""
    
    PARALLEL = "parallel"
    """Query split to multiple agents in parallel, results merged. Useful for multi-perspective analysis."""
    
    APPROVAL_CHAIN = "approval_chain"
    """Sequential approval workflow (requester → reviewer → approver → executor). Each stage can approve/reject."""


# ============================================================================
# Request Models
# ============================================================================

class WorkflowRequest(BaseModel):
    """
    Request to execute a multi-agent workflow.
    
    Fields:
    - message: The user query or request
    - thread_id: Required. Thread ID for conversation continuity
    - max_handoffs: Optional. Override default max handoffs (default: workflow setting)
    - stream: Whether to stream response (default: True)
    """
    message: str = Field(..., description="User query or request")
    thread_id: str = Field(..., description="Required thread ID for conversation continuity")
    max_handoffs: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional override of workflow max_handoffs (1-10)"
    )
    stream: bool = Field(default=True, description="Stream response via SSE")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the top 5 customers by revenue and what should we focus on for retention?",
                "thread_id": "thread_xyz123",
                "max_handoffs": 3,
                "stream": True
            }
        }


# ============================================================================
# Response Models
# ============================================================================

class WorkflowResponse(BaseModel):
    """
    Response from a multi-agent workflow execution.
    
    Fields:
    - workflow_id: The workflow that executed
    - final_response: The final answer to the user's query
    - primary_agent: First specialist agent used
    - handoff_path: List of agent IDs in execution order
    - satisfaction_score: Evaluator's confidence (0.0-1.0)
    - evaluator_reasoning: Why evaluator determined satisfaction
    - max_attempts_reached: Whether max_handoffs limit was hit
    - execution_time_ms: Total execution time
    """
    workflow_id: str = Field(description="ID of the workflow executed")
    final_response: str = Field(description="Final response to user query")
    primary_agent: str = Field(description="First specialist agent used")
    handoff_path: List[str] = Field(description="Path of agents in execution order")
    satisfaction_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Evaluator confidence score"
    )
    evaluator_reasoning: Optional[str] = Field(
        default=None,
        description="Evaluator's assessment reasoning"
    )
    max_attempts_reached: bool = Field(default=False, description="Whether max_handoffs limit was hit")
    execution_time_ms: float = Field(description="Total execution time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "intelligent-handoff",
                "final_response": "Your top 5 customers are... with these retention recommendations...",
                "primary_agent": "data-agent",
                "handoff_path": ["router", "data-agent", "analyst", "evaluator"],
                "satisfaction_score": 0.92,
                "evaluator_reasoning": "Response comprehensively addresses query with actionable recommendations",
                "max_attempts_reached": False,
                "execution_time_ms": 3250.5
            }
        }


class AgentInteraction(BaseModel):
    """
    Single agent interaction in a workflow.
    
    Fields:
    - agent_id: Which agent handled this step
    - input: What was sent to the agent
    - output: What the agent returned
    - tool_calls: Any tools the agent called
    - execution_time_ms: How long this step took
    """
    agent_id: str = Field(description="Agent that handled this interaction")
    input: str = Field(description="User message/input to agent")
    output: str = Field(description="Agent's response")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools called by agent")
    execution_time_ms: float = Field(description="Execution time for this step")


class WorkflowTraceMetadata(BaseModel):
    """
    Complete trace metadata for a workflow execution.
    
    Includes detailed information about the entire workflow run:
    - Agent interactions in order
    - Tool calls and their results
    - Timing information
    - Evaluator assessment
    - Handoff reasoning
    
    This is shown in the trace panel on the frontend, separate from the chat message.
    """
    workflow_id: str = Field(description="Workflow ID")
    thread_id: str = Field(description="Thread ID")
    handoff_path: List[str] = Field(description="Path of agents: [router, agent1, evaluator, router, agent2, evaluator]")
    agent_interactions: List[AgentInteraction] = Field(
        default_factory=list,
        description="Detailed interaction with each agent"
    )
    total_handoffs: int = Field(description="Number of times a handoff occurred")
    max_handoffs_configured: int = Field(description="Max handoffs limit for this workflow")
    max_attempts_reached: bool = Field(default=False, description="Whether max limit was hit")
    evaluator_assessments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Each evaluator assessment in order"
    )
    final_satisfaction_score: Optional[float] = Field(
        default=None,
        description="Final evaluator satisfaction score"
    )
    final_evaluator_reasoning: Optional[str] = Field(
        default=None,
        description="Final evaluator reasoning"
    )
    total_execution_time_ms: float = Field(description="Total workflow execution time")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="When workflow started")
    end_time: Optional[datetime] = Field(default=None, description="When workflow completed")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "intelligent-handoff",
                "thread_id": "thread_xyz123",
                "handoff_path": ["router", "data-agent", "analyst", "evaluator"],
                "agent_interactions": [
                    {
                        "agent_id": "router",
                        "input": "What are top 5 customers?",
                        "output": "Routing to data-agent for customer data retrieval",
                        "tool_calls": [],
                        "execution_time_ms": 150.2
                    }
                ],
                "total_handoffs": 2,
                "max_handoffs_configured": 3,
                "max_attempts_reached": False,
                "evaluator_assessments": [
                    {
                        "satisfied": False,
                        "reasoning": "Data provided but no analysis"
                    },
                    {
                        "satisfied": True,
                        "reasoning": "Complete answer with insights and recommendations"
                    }
                ],
                "final_satisfaction_score": 0.92,
                "final_evaluator_reasoning": "Response fully addresses query",
                "total_execution_time_ms": 3250.5,
                "start_time": "2025-10-29T10:30:00Z",
                "end_time": "2025-10-29T10:30:03.25Z"
            }
        }
