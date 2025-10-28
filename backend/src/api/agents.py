"""
Agent Management API

RESTful endpoints for managing agents:
- List agents with filtering (GET /api/agents)
- Get agent details (GET /api/agents/{agent_id})
- Create agent (POST /api/agents) - Admin only
- Update agent (PUT /api/agents/{agent_id}) - Admin only
- Delete agent (DELETE /api/agents/{agent_id}) - Admin only
- Activate agent (POST /api/agents/{agent_id}/activate) - Admin only
- Deactivate agent (POST /api/agents/{agent_id}/deactivate) - Admin only
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query, Depends, status as http_status, Body
from fastapi.responses import JSONResponse

from src.persistence.agents import get_agent_repository
from src.persistence.models import (
    AgentMetadata,
    AgentStatus,
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ============================================================================
# Helper Functions
# ============================================================================

def get_agent_repo():
    """Dependency to get agent repository."""
    logger.info("[DEPENDENCY] get_agent_repo called")
    try:
        repo = get_agent_repository()
        logger.info(f"[DEPENDENCY] Returning repo: {repo}")
        return repo
    except RuntimeError as e:
        # Cosmos DB not available - return None to trigger mock mode
        logger.warning(f"Agent repository not available: {e}")
        return None


# TODO: Implement proper admin authentication
# For now, this is a placeholder
async def require_admin():
    """
    Dependency that checks if the current user is an admin.
    
    In production, this should validate OAuth tokens and check user roles.
    For now, it's a placeholder that always succeeds.
    """
    # TODO: Implement actual authentication check
    # - Extract bearer token from Authorization header
    # - Validate token with Azure AD / OAuth provider
    # - Check if user has "admin" role
    # - Raise HTTPException(403) if not authorized
    pass


# ============================================================================
# Test Endpoints
# ============================================================================

@router.put("/test-put/{agent_id}")
def test_put(agent_id: str = Path(...)):
    """Test PUT endpoint to verify routing."""
    logger.info(f"[TEST PUT] Called with agent_id: {agent_id}")
    return {"status": "ok", "agent_id": agent_id}


# ============================================================================
# Public Endpoints (No Authentication Required)
# ============================================================================

@router.get("", response_model=AgentListResponse)
def list_agents(
    status: Optional[AgentStatus] = Query(default=AgentStatus.ACTIVE, description="Filter by status"),
    is_public: Optional[bool] = Query(default=None, description="Filter by visibility"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of agents to return"),
    offset: int = Query(default=0, ge=0, description="Number of agents to skip"),
    repo = Depends(get_agent_repo)
):
    """
    List all agents with optional filtering.
    By default, only active agents are returned.
    
    Query Parameters:
    - status: Filter by agent status (active, inactive, maintenance) - defaults to active
    - is_public: Filter by visibility (true for public, false for private)
    - limit: Maximum number of agents to return (1-100, default 50)
    - offset: Number of agents to skip for pagination (default 0)
    
    Returns:
    - agents: List of agent metadata
    - total: Total number of agents matching filters
    - limit: Page size used
    - offset: Offset used
    """
    # Mock mode when Cosmos DB is not available
    if repo is None:
        logger.info("Using mock agent data (Cosmos DB not available)")
        from src.persistence.seed_agents import get_default_agents
        
        mock_agents = get_default_agents()
        
        # Apply filters
        if status:
            mock_agents = [a for a in mock_agents if a.status == status]
        if is_public is not None:
            mock_agents = [a for a in mock_agents if a.is_public == is_public]
        
        # Apply pagination
        total = len(mock_agents)
        mock_agents = mock_agents[offset:offset + limit]
        
        return AgentListResponse(
            agents=mock_agents,
            total=total,
            limit=limit,
            offset=offset
        )
    
    try:
        # Get agents
        agents = repo.list(
            status=status,
            is_public=is_public,
            limit=limit,
            offset=offset
        )
        
        # Get total count
        total = repo.count(status=status, is_public=is_public)
        
        return AgentListResponse(
            agents=agents,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents"
        )


@router.get("/{agent_id}", response_model=AgentMetadata)
def get_agent(
    agent_id: str = Path(..., description="Agent identifier"),
    repo = Depends(get_agent_repo)
):
    """
    Get details for a specific agent.
    
    Path Parameters:
    - agent_id: Unique agent identifier (e.g., "support-triage")
    
    Returns:
    - Agent metadata including configuration, tools, capabilities, and statistics
    
    Raises:
    - 404: Agent not found
    """
    try:
        agent = repo.get(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent"
        )


# ============================================================================
# Admin Endpoints (Authentication Required)
# ============================================================================

@router.post("", response_model=AgentMetadata, status_code=http_status.HTTP_201_CREATED)
def create_agent(
    request: AgentCreateRequest,
    repo = Depends(get_agent_repo),
    _admin = Depends(require_admin)
):
    """
    Create a new agent. (Admin only)
    
    Request Body:
    - id: Unique agent identifier (e.g., "my-agent")
    - name: Display name
    - description: Agent description
    - system_prompt: System prompt/instructions
    - model: Azure OpenAI model name (default: "gpt-4o")
    - temperature: Temperature setting (default: 0.7)
    - max_tokens: Max tokens per response (optional)
    - max_messages: Sliding window size (default: 20)
    - tools: List of tool configurations (default: [])
    - capabilities: List of capability strings (default: [])
    - is_public: Whether agent is visible to all users (default: true)
    
    Returns:
    - Created agent metadata
    
    Raises:
    - 400: Agent ID already exists
    - 403: Not authorized (admin only)
    - 500: Creation failed
    """
    try:
        # Check if agent already exists
        existing = repo.get(request.id)
        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Agent already exists: {request.id}"
            )
        
        # Create agent metadata
        agent = AgentMetadata(
            id=request.id,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            max_messages=request.max_messages,
            tools=request.tools,
            capabilities=request.capabilities,
            is_public=request.is_public,
            status=AgentStatus.INACTIVE  # Start as inactive, activate explicitly
        )
        
        # Save to database
        created_agent = repo.upsert(agent)
        
        logger.info(f"Created agent: {created_agent.id}")
        return created_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )


@router.put("/{agent_id}")
def update_agent(
    agent_id: str = Path(..., description="Agent identifier"),
    request: AgentUpdateRequest = Body(...),
    repo = Depends(get_agent_repo)
):
    """Update an agent's configuration."""
    
    try:
        updated_agent = repo.update(agent_id, request)
        
        if not updated_agent:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        logger.info(f"Updated agent: {agent_id}")
        return updated_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )


@router.delete("/{agent_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: str = Path(..., description="Agent identifier"),
    hard_delete: bool = Query(default=False, description="Permanently delete (default: soft delete)"),
    repo = Depends(get_agent_repo),
    _admin = Depends(require_admin)
):
    """
    Delete an agent. (Admin only)
    
    Path Parameters:
    - agent_id: Agent identifier to delete
    
    Query Parameters:
    - hard_delete: If true, permanently delete. If false, set status to inactive (default: false)
    
    Raises:
    - 404: Agent not found
    - 403: Not authorized (admin only)
    - 500: Deletion failed
    """
    try:
        success = repo.delete(agent_id, hard_delete=hard_delete)
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        delete_type = "hard" if hard_delete else "soft"
        logger.info(f"{delete_type.capitalize()} deleted agent: {agent_id}")
        
        # Return 204 No Content - don't return any response body
        return
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )


@router.post("/{agent_id}/activate", response_model=AgentMetadata)
def activate_agent(
    agent_id: str = Path(..., description="Agent identifier"),
    repo = Depends(get_agent_repo),
    _admin = Depends(require_admin)
):
    """
    Activate an agent (set status to ACTIVE). (Admin only)
    
    Path Parameters:
    - agent_id: Agent identifier to activate
    
    Returns:
    - Updated agent metadata with status=active
    
    Raises:
    - 404: Agent not found
    - 403: Not authorized (admin only)
    - 500: Activation failed
    """
    try:
        success = repo.activate(agent_id)
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        # Get updated agent
        agent = repo.get(agent_id)
        
        logger.info(f"Activated agent: {agent_id}")
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate agent {agent_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate agent"
        )


@router.post("/{agent_id}/deactivate", response_model=AgentMetadata)
def deactivate_agent(
    agent_id: str = Path(..., description="Agent identifier"),
    repo = Depends(get_agent_repo),
    _admin = Depends(require_admin)
):
    """
    Deactivate an agent (set status to INACTIVE). (Admin only)
    
    Path Parameters:
    - agent_id: Agent identifier to deactivate
    
    Returns:
    - Updated agent metadata with status=inactive
    
    Raises:
    - 404: Agent not found
    - 403: Not authorized (admin only)
    - 500: Deactivation failed
    """
    try:
        success = repo.deactivate(agent_id)
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        # Get updated agent
        agent = repo.get(agent_id)
        
        logger.info(f"Deactivated agent: {agent_id}")
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate agent {agent_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate agent"
        )
