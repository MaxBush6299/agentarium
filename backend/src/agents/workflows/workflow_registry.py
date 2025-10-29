"""
Workflow Registry

Defines available workflows and their configuration.

Workflow Types:
- handoff: Multi-tier routing with quality evaluation (intelligent re-routing)
- sequential: Linear pipeline (agent1 → agent2 → agent3 → ...)
- parallel: Split query to multiple agents, merge results
- approval_chain: Sequential approval workflow (requester → reviewer → approver)

Structure:
Each workflow defines:
- id: Unique workflow identifier
- type: Workflow pattern type (handoff, sequential, parallel, approval_chain)
- name: Display name
- description: Human-readable description
- coordinator: Entry point agent (may be None for purely sequential workflows)
- participants: All agents involved
- max_handoffs: Maximum iterations (prevents infinite loops)
- routing_rules: Constraints that apply to this workflow
"""

from typing import Dict, Any, Optional
from enum import Enum


# ============================================================================
# Workflow Type Enumeration
# ============================================================================

class WorkflowType(str, Enum):
    """Workflow execution patterns."""
    HANDOFF = "handoff"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    APPROVAL_CHAIN = "approval_chain"


# ============================================================================
# Workflow Definitions
# ============================================================================

WORKFLOW_REGISTRY = {
    "intelligent-handoff": {
        "id": "intelligent-handoff",
        "type": "handoff",
        "name": "Intelligent Handoff Workflow",
        "description": "Multi-tier routing with quality evaluation and intelligent re-routing. Routes queries through specialists (data-agent, analyst, order-agent) with quality evaluation at the end. If evaluator determines response is unsatisfactory, routes back to router for another attempt.",
        "active": True,
        "coordinator": "router",
        "participants": [
            "router",           # Entry point and re-routing coordinator
            "data-agent",       # Database queries and data retrieval
            "analyst",          # Business intelligence and insights
            "order-agent",      # Order placement and fulfillment
            "evaluator",        # Quality assessment and satisfaction evaluation
        ],
        "max_handoffs": 3,
        "routing_rules": {
            "data_agent_requires_analyst": True,  # If data-agent used → must route to analyst
            "always_end_with_evaluator": True,    # All paths must end with evaluator
            "allow_reroute_if_unsatisfied": True, # Evaluator can route back to router if unsatisfied
        },
        "metadata": {
            "version": "1.0.0",
            "created_at": "2025-10-29",
            "tags": ["multi-agent", "handoff", "evaluation", "quality-control"],
        }
    },
    "data-analysis-pipeline": {
        "id": "data-analysis-pipeline",
        "type": "sequential",
        "name": "Data Analysis Pipeline",
        "description": "Sequential processing pipeline: data-agent retrieves data → analyst performs analysis → evaluator validates results. Each agent receives output from previous.",
        "active": False,
        "coordinator": None,  # Sequential workflows don't need coordinator
        "participants": [
            "data-agent",       # Step 1: Data retrieval
            "analyst",          # Step 2: Analysis
            "evaluator",        # Step 3: Validation
        ],
        "max_handoffs": 1,     # Sequential, no loops
        "routing_rules": {
            "sequence": ["data-agent", "analyst", "evaluator"],
            "pass_output_as_input": True,  # Each step receives previous output
        },
        "metadata": {
            "version": "1.0.0",
            "created_at": "2025-10-29",
            "tags": ["sequential", "data-driven", "analysis"],
        }
    },
    "multi-perspective-analysis": {
        "id": "multi-perspective-analysis",
        "type": "parallel",
        "name": "Multi-Perspective Analysis",
        "description": "Parallel analysis: query is sent to data-agent, analyst, and order-agent simultaneously. Results are merged and evaluated. Useful for comprehensive business analysis.",
        "active": False,
        "coordinator": None,  # Parallel workflows use merge logic
        "participants": [
            "data-agent",       # Perspective 1: Data view
            "analyst",          # Perspective 2: BI/analysis view
            "order-agent",      # Perspective 3: Business operations view
            "evaluator",        # Final: Consolidate perspectives
        ],
        "max_handoffs": 1,
        "routing_rules": {
            "parallel_agents": ["data-agent", "analyst", "order-agent"],
            "merge_strategy": "consolidate",  # Combine perspectives
            "final_step": "evaluator",
        },
        "metadata": {
            "version": "1.0.0",
            "created_at": "2025-10-29",
            "tags": ["parallel", "multi-perspective", "analysis"],
        }
    },
    "change-approval-workflow": {
        "id": "change-approval-workflow",
        "type": "approval_chain",
        "name": "Change Approval Workflow",
        "description": "Sequential approval workflow for operational changes. Request → Data validation → Manager review → Execution. Can be rejected at any stage.",
        "active": False,
        "coordinator": "router",  # Router can restart/escalate
        "participants": [
            "data-agent",       # Validate request data
            "analyst",          # Business impact analysis
            "order-agent",      # Execute approved order
        ],
        "max_handoffs": 3,
        "routing_rules": {
            "sequence": ["data-agent", "analyst", "order-agent"],
            "require_approval_at_each_step": True,
            "rejection_returns_to": "router",
        },
        "metadata": {
            "version": "1.0.0",
            "created_at": "2025-10-29",
            "tags": ["approval", "sequential", "operational"],
        }
    }
}



# ============================================================================
# Public API
# ============================================================================

def get_available_workflows() -> Dict[str, Dict[str, Any]]:
    """
    Get all active available workflows.
    
    Returns:
        Dictionary mapping workflow_id to workflow configuration (only active workflows)
    """
    return {
        workflow_id: config 
        for workflow_id, config in WORKFLOW_REGISTRY.items()
        if config.get("active", False)
    }


def get_workflow_config(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific workflow.
    
    Args:
        workflow_id: ID of the workflow (e.g., "intelligent-handoff")
        
    Returns:
        Workflow configuration dict, or None if not found
    """
    return WORKFLOW_REGISTRY.get(workflow_id)


def workflow_exists(workflow_id: str) -> bool:
    """
    Check if a workflow is registered.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        True if workflow exists, False otherwise
    """
    return workflow_id in WORKFLOW_REGISTRY


def validate_workflow_id(workflow_id: str) -> bool:
    """
    Validate that a workflow_id is valid.
    
    Args:
        workflow_id: ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not workflow_id:
        return False
    if not isinstance(workflow_id, str):
        return False
    return workflow_exists(workflow_id)


def get_workflow_participants(workflow_id: str) -> Optional[list]:
    """
    Get list of participant agents for a workflow.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        List of agent IDs, or None if workflow not found
    """
    config = get_workflow_config(workflow_id)
    return config.get("participants") if config else None


def get_workflow_coordinator(workflow_id: str) -> Optional[str]:
    """
    Get the coordinator agent for a workflow.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Agent ID of the coordinator, or None if workflow not found
    """
    config = get_workflow_config(workflow_id)
    return config.get("coordinator") if config else None


def get_workflow_rules(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Get routing rules for a workflow.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Routing rules dict, or None if workflow not found
    """
    config = get_workflow_config(workflow_id)
    return config.get("routing_rules") if config else None


def get_max_handoffs(workflow_id: str) -> int:
    """
    Get maximum handoff limit for a workflow.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Maximum handoffs (default 3 if workflow not found)
    """
    config = get_workflow_config(workflow_id)
    return config.get("max_handoffs", 3) if config else 3
