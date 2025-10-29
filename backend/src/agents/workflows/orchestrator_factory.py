"""
Workflow Orchestrator Factory

Factory pattern for creating appropriate orchestrator instances based on workflow type.

Provides:
- create_orchestrator(): Factory function that routes to correct orchestrator class
- Registry of orchestrator classes mapped to workflow types
- Validation of workflow type compatibility

Usage:
    orchestrator = create_orchestrator(
        workflow_id="intelligent-handoff",
        workflow_config=get_workflow_config("intelligent-handoff"),
        chat_client=client
    )
    
    response, metadata = await orchestrator.execute(
        message="user query",
        thread_id="xyz"
    )
"""

import logging
from typing import Optional, Dict, Type, Any

from src.agents.workflows.workflow_registry import get_workflow_config, WorkflowType
from src.agents.workflows.base_orchestrator import BaseWorkflowOrchestrator

logger = logging.getLogger(__name__)


# Forward declarations (actual implementations imported below after base class defined)
# This avoids circular import issues
ORCHESTRATOR_REGISTRY: Dict[str, Type[BaseWorkflowOrchestrator]] = {}


def register_orchestrator(
    workflow_type: str,
    orchestrator_class: Type[BaseWorkflowOrchestrator]
):
    """
    Register an orchestrator class for a workflow type.
    
    Args:
        workflow_type: Type identifier (e.g., WorkflowType.HANDOFF)
        orchestrator_class: Class implementing BaseWorkflowOrchestrator
    """
    ORCHESTRATOR_REGISTRY[workflow_type] = orchestrator_class
    logger.info(f"Registered {orchestrator_class.__name__} for workflow type '{workflow_type}'")


async def create_orchestrator(
    workflow_id: str,
    workflow_config: Optional[Dict[str, Any]] = None,
    chat_client: Any = None,
) -> BaseWorkflowOrchestrator:
    """
    Factory function to create appropriate orchestrator for a workflow.
    
    This function:
    1. Validates the workflow_id
    2. Retrieves workflow configuration (from registry or parameter)
    3. Extracts the workflow type
    4. Looks up the appropriate orchestrator class
    5. Instantiates and returns the orchestrator
    
    Args:
        workflow_id: ID of the workflow (e.g., "intelligent-handoff")
        workflow_config: Override workflow config (optional, usually loaded from registry)
        chat_client: Chat client for agent invocation
        
    Returns:
        Initialized orchestrator instance
        
    Raises:
        ValueError: If workflow_id not found or type not supported
        
    Example:
        # Create orchestrator for intelligent-handoff workflow
        orchestrator = await create_orchestrator(
            workflow_id="intelligent-handoff",
            chat_client=client
        )
        
        # Create orchestrator for sequential workflow
        orchestrator = await create_orchestrator(
            workflow_id="data-analysis-pipeline",
            chat_client=client
        )
    """
    logger.info(f"Creating orchestrator for workflow '{workflow_id}'")
    
    # Load config if not provided
    if workflow_config is None:
        workflow_config = get_workflow_config(workflow_id)
        if workflow_config is None:
            raise ValueError(f"Workflow '{workflow_id}' not found in registry")
    
    # Extract workflow type
    workflow_type = workflow_config.get("type")
    if not workflow_type:
        raise ValueError(f"Workflow '{workflow_id}' has no 'type' field in configuration")
    
    # Look up orchestrator class
    if workflow_type not in ORCHESTRATOR_REGISTRY:
        raise ValueError(
            f"No orchestrator registered for workflow type '{workflow_type}'. "
            f"Available types: {list(ORCHESTRATOR_REGISTRY.keys())}"
        )
    
    orchestrator_class = ORCHESTRATOR_REGISTRY[workflow_type]
    logger.info(f"Using {orchestrator_class.__name__} for type '{workflow_type}'")
    
    # Create and return orchestrator instance
    orchestrator = orchestrator_class(
        workflow_id=workflow_id,
        workflow_config=workflow_config,
        chat_client=chat_client,
    )
    
    return orchestrator


# Import orchestrator implementations and register them
# These imports happen after factory functions are defined to avoid circular imports
try:
    from src.agents.workflows.handoff_orchestrator import HandoffOrchestrator
    register_orchestrator(WorkflowType.HANDOFF, HandoffOrchestrator)
except ImportError as e:
    logger.warning(f"Could not import HandoffOrchestrator: {e}")

try:
    from src.agents.workflows.sequential_orchestrator import SequentialOrchestrator
    register_orchestrator(WorkflowType.SEQUENTIAL, SequentialOrchestrator)
except ImportError as e:
    logger.warning(f"Could not import SequentialOrchestrator: {e}")

try:
    from src.agents.workflows.parallel_orchestrator import ParallelOrchestrator
    register_orchestrator(WorkflowType.PARALLEL, ParallelOrchestrator)
except ImportError as e:
    logger.warning(f"Could not import ParallelOrchestrator: {e}")

try:
    from src.agents.workflows.approval_orchestrator import ApprovalChainOrchestrator
    register_orchestrator(WorkflowType.APPROVAL_CHAIN, ApprovalChainOrchestrator)
except ImportError as e:
    logger.warning(f"Could not import ApprovalChainOrchestrator: {e}")
