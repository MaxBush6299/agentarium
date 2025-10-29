"""
Multi-Agent Workflow Infrastructure

Provides HandoffBuilder-based workflow orchestration for multiple workflow patterns.

Supported Workflow Types:
- handoff: Intelligent routing with quality evaluation and re-routing
- sequential: Linear pipeline (agent1 → agent2 → agent3 → ...)
- parallel: Parallel branching with merge (split → process → combine)
- approval_chain: Sequential approval workflow with rejection handling

Key Components:
- workflow_registry.py - Registry of available workflows
- workflow_models.py - Pydantic models for requests/responses
- base_orchestrator.py - Abstract base class for orchestrators
- orchestrator_factory.py - Factory pattern for creating orchestrators
- handoff_orchestrator.py - Handoff pattern implementation
- sequential_orchestrator.py - Sequential pipeline implementation
- parallel_orchestrator.py - Parallel branching implementation
- approval_orchestrator.py - Approval chain implementation
- workflow_orchestrator.py - High-level orchestrator (legacy)
- handoff_workflow.py - High-level workflow handler

Architecture:
The workflow system supports multiple orchestration patterns via a registry-based
factory design. Each workflow type can define custom routing rules and constraints.

Usage - Factory Pattern (Recommended):
    from src.agents.workflows import create_orchestrator
    
    # Create orchestrator for any workflow type
    orchestrator = await create_orchestrator(
        workflow_id="intelligent-handoff",
        chat_client=client
    )
    
    response, metadata = await orchestrator.execute(
        message="user query",
        thread_id="xyz123"
    )

Usage - List Workflows:
    from src.agents.workflows import get_available_workflows
    
    workflows = get_available_workflows()
    for workflow_id, config in workflows.items():
        print(f"{workflow_id}: {config['type']}")
"""

# Workflow types and models
from src.agents.workflows.workflow_models import (
    WorkflowType,
    WorkflowRequest,
    WorkflowResponse,
    AgentInteraction,
    WorkflowTraceMetadata,
)

# Registry
from src.agents.workflows.workflow_registry import (
    get_available_workflows,
    get_workflow_config,
    workflow_exists,
    validate_workflow_id,
    get_workflow_participants,
    get_workflow_coordinator,
    get_workflow_rules,
    get_max_handoffs,
    WORKFLOW_REGISTRY,
)

# Base and factory
from src.agents.workflows.base_orchestrator import BaseWorkflowOrchestrator
from src.agents.workflows.orchestrator_factory import (
    create_orchestrator,
    register_orchestrator,
)

# Orchestrator implementations
from src.agents.workflows.handoff_orchestrator import HandoffOrchestrator
from src.agents.workflows.sequential_orchestrator import SequentialOrchestrator
from src.agents.workflows.parallel_orchestrator import ParallelOrchestrator
from src.agents.workflows.approval_orchestrator import ApprovalChainOrchestrator

# Handler
from src.agents.workflows.handoff_workflow import WorkflowHandler

__all__ = [
    # Workflow types
    "WorkflowType",
    
    # Models
    "WorkflowRequest",
    "WorkflowResponse",
    "AgentInteraction",
    "WorkflowTraceMetadata",
    
    # Registry
    "get_available_workflows",
    "get_workflow_config",
    "workflow_exists",
    "validate_workflow_id",
    "get_workflow_participants",
    "get_workflow_coordinator",
    "get_workflow_rules",
    "get_max_handoffs",
    "WORKFLOW_REGISTRY",
    
    # Factory
    "create_orchestrator",
    "register_orchestrator",
    
    # Orchestrators
    "BaseWorkflowOrchestrator",
    "HandoffOrchestrator",
    "SequentialOrchestrator",
    "ParallelOrchestrator",
    "ApprovalChainOrchestrator",
    
    # Handler
    "WorkflowHandler",
]
