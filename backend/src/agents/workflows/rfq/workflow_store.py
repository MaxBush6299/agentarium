"""
Temporary workflow instance storage for Phase 6 human-in-the-loop pause/resume.

This is a simple in-memory store to keep workflow instances alive between
the initial run and the approval response. In production, this should be
replaced with proper workflow state persistence (e.g., Redis, CosmosDB).

Usage:
    # Store workflow when it pauses at Phase 6
    store_workflow_instance(workflow_id, workflow)
    
    # Retrieve workflow when approval action received
    workflow = get_workflow_instance(workflow_id)
    
    # Resume workflow
    await workflow.send_responses_streaming({request_id: approval_decision})
"""

from typing import Dict, Any, Optional
from agent_framework import Workflow

# Global in-memory store for workflow instances
# Key: workflow_exec_id, Value: (workflow_instance, request_id)
_workflow_store: Dict[str, tuple[Workflow, Optional[str]]] = {}


def store_workflow_instance(
    workflow_id: str,
    workflow: Workflow,
    request_id: Optional[str] = None
) -> None:
    """
    Store workflow instance for later retrieval.
    
    Args:
        workflow_id: Unique workflow execution ID
        workflow: Workflow instance
        request_id: Optional request ID for Phase 6 approval
    """
    _workflow_store[workflow_id] = (workflow, request_id)


def get_workflow_instance(workflow_id: str) -> Optional[tuple[Workflow, Optional[str]]]:
    """
    Retrieve stored workflow instance.
    
    Args:
        workflow_id: Unique workflow execution ID
        
    Returns:
        Tuple of (workflow, request_id) if found, None otherwise
    """
    return _workflow_store.get(workflow_id)


def remove_workflow_instance(workflow_id: str) -> None:
    """
    Remove workflow instance from store.
    
    Args:
        workflow_id: Unique workflow execution ID
    """
    _workflow_store.pop(workflow_id, None)


def list_workflow_instances() -> Dict[str, tuple[Workflow, Optional[str]]]:
    """
    List all stored workflow instances.
    
    Returns:
        Dictionary of workflow_id -> (workflow, request_id)
    """
    return dict(_workflow_store)
