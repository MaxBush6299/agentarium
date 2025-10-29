"""
Base Workflow Orchestrator

Abstract base class defining the interface for all workflow orchestrators.

Responsibilities:
- Define standard workflow execution interface
- Provide common utilities for orchestrators
- Enforce consistent response formats
- Track execution metadata

Subclasses:
- HandoffOrchestrator: Implements handoff/routing pattern with quality evaluation
- SequentialOrchestrator: Implements linear pipeline execution
- ParallelOrchestrator: Implements parallel branching and merging
- ApprovalChainOrchestrator: Implements approval workflow with rejection handling
"""

import logging
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional

from src.agents.workflows.workflow_models import (
    WorkflowTraceMetadata,
    AgentInteraction
)

logger = logging.getLogger(__name__)


class BaseWorkflowOrchestrator(ABC):
    """
    Abstract base class for workflow orchestrators.
    
    Defines the interface that all orchestrators must implement and
    provides common utility methods.
    """
    
    def __init__(
        self,
        workflow_id: str,
        workflow_config: Dict[str, Any],
        chat_client: Any = None,
    ):
        """
        Initialize base orchestrator.
        
        Args:
            workflow_id: ID of the workflow (e.g., "intelligent-handoff")
            workflow_config: Workflow configuration from registry
            chat_client: Chat client for agent invocation (e.g., Azure OpenAI)
        """
        self.workflow_id = workflow_id
        self.workflow_config = workflow_config
        self.chat_client = chat_client
        self.interactions: list[AgentInteraction] = []
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        self.logger.info(f"Initialized {self.__class__.__name__} for workflow '{workflow_id}'")
    
    @abstractmethod
    async def execute(
        self,
        message: str,
        thread_id: str,
        max_handoffs: Optional[int] = None,
    ) -> Tuple[str, WorkflowTraceMetadata]:
        """
        Execute the workflow.
        
        This method must be implemented by subclasses to define
        the specific execution pattern (handoff, sequential, parallel, etc.).
        
        Args:
            message: User message to process
            thread_id: Thread ID for persistence
            max_handoffs: Override max handoffs from config
            
        Returns:
            Tuple of (final_response, trace_metadata)
            
        Raises:
            Exception: If execution fails
        """
        pass
    
    async def invoke_agent(
        self,
        agent_id: str,
        message: str,
        thread_id: str,
    ) -> str:
        """
        Invoke a single agent and capture interaction.
        
        Args:
            agent_id: ID of agent to invoke
            message: Message to send to agent
            thread_id: Thread ID for context
            
        Returns:
            Agent response message
            
        TODO: Implement actual agent invocation
        Current: Placeholder returning mock response
        """
        self.logger.info(f"Invoking agent '{agent_id}' with message: {message[:50]}...")
        
        # TODO: Get agent from repository
        # TODO: Format message with thread context
        # TODO: Stream response and capture tool calls
        # TODO: Create AgentInteraction and add to self.interactions
        
        # Placeholder response
        response = f"Response from {agent_id}"
        
        interaction = AgentInteraction(
            agent_id=agent_id,
            input=message,
            output=response,
            tool_calls=[],
            execution_time_ms=100.0
        )
        self.interactions.append(interaction)
        
        self.logger.info(f"Agent '{agent_id}' responded")
        return response
    
    def _build_trace_metadata(
        self,
        final_response: str,
        primary_agent: str,
        handoff_path: list[str],
        satisfaction_score: float = 1.0,
        evaluator_reasoning: str = "",
        max_attempts_reached: bool = False,
        thread_id: str = "",
    ) -> WorkflowTraceMetadata:
        """
        Build trace metadata for workflow execution.
        
        Args:
            final_response: Final response to user
            primary_agent: Primary agent handling this request
            handoff_path: List of agents in execution order
            satisfaction_score: Quality score (0.0-1.0)
            evaluator_reasoning: Evaluator's assessment
            max_attempts_reached: Whether max handoffs was reached
            thread_id: Thread ID for context
            
        Returns:
            Populated WorkflowTraceMetadata
        """
        return WorkflowTraceMetadata(
            workflow_id=self.workflow_id,
            thread_id=thread_id,
            handoff_path=handoff_path,
            agent_interactions=self.interactions,
            total_handoffs=len(handoff_path) - 1,
            max_handoffs_configured=self.workflow_config.get("max_handoffs", 3),
            total_execution_time_ms=0.0,  # TODO: Calculate
            max_attempts_reached=max_attempts_reached,
            evaluator_assessments=[],  # TODO: Populate from evaluator responses
            final_satisfaction_score=satisfaction_score,
            final_evaluator_reasoning=evaluator_reasoning,
        )
    
    def _get_coordinator(self) -> Optional[str]:
        """Get coordinator agent for this workflow."""
        return self.workflow_config.get("coordinator")
    
    def _get_participants(self) -> list[str]:
        """Get all participant agents for this workflow."""
        return self.workflow_config.get("participants", [])
    
    def _get_routing_rules(self) -> Dict[str, Any]:
        """Get routing rules for this workflow."""
        return self.workflow_config.get("routing_rules", {})
    
    def _get_max_handoffs(self, override: Optional[int] = None) -> int:
        """Get max handoffs (use override if provided, else config)."""
        if override is not None:
            return override
        return self.workflow_config.get("max_handoffs", 3)
