"""
API endpoints for managing agent cards.

Provides REST API for CRUD operations on A2A protocol agent cards.
This allows the frontend to dynamically register new agents.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from .agent_cards import (
    get_agent_card_store,
    AgentCard,
    AgentSkill,
    AgentCapabilities
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-cards", tags=["agent-cards"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateAgentCardRequest(BaseModel):
    """Request model for creating a new agent card"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Agent display name")
    description: str = Field(..., description="Agent description")
    skills: List[Dict[str, Any]] = Field(..., description="List of agent skills")
    provider: Optional[str] = Field(None, description="Provider organization name")
    version: str = Field(default="1.0.0", description="Agent version")
    base_url: str = Field(..., description="Base URL for A2A endpoint")


class UpdateAgentCardRequest(BaseModel):
    """Request model for updating an existing agent card"""
    name: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[Dict[str, Any]]] = None
    provider: Optional[str] = None
    version: Optional[str] = None


class AgentCardResponse(BaseModel):
    """Response model for agent card operations"""
    agent_id: str
    card: AgentCard


class AgentCardListResponse(BaseModel):
    """Response model for listing agent cards"""
    agent_ids: List[str]
    count: int


# ============================================================================
# Agent Card Management Endpoints
# ============================================================================

@router.get("/", response_model=AgentCardListResponse)
async def list_agent_cards():
    """
    List all registered agent cards.
    
    Returns:
        List of agent IDs and count
    """
    try:
        store = get_agent_card_store()
        agent_ids = store.list_agent_ids()
        
        return AgentCardListResponse(
            agent_ids=agent_ids,
            count=len(agent_ids)
        )
    except Exception as e:
        logger.error(f"Failed to list agent cards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agent cards"
        )


@router.get("/{agent_id}", response_model=AgentCardResponse)
async def get_agent_card(agent_id: str):
    """
    Get a specific agent card by ID.
    
    Args:
        agent_id: Unique identifier for the agent
        
    Returns:
        Agent card details
    """
    try:
        store = get_agent_card_store()
        card = store.get_agent_card(agent_id)
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent card not found: {agent_id}"
            )
        
        return AgentCardResponse(
            agent_id=agent_id,
            card=card
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent card '{agent_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent card: {agent_id}"
        )


@router.post("/", response_model=AgentCardResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_card(request: CreateAgentCardRequest):
    """
    Create a new agent card.
    
    This endpoint allows the frontend to dynamically register new agents
    by providing their metadata and capabilities.
    
    Args:
        request: Agent card creation request
        
    Returns:
        Created agent card
    """
    try:
        store = get_agent_card_store()
        
        # Check if agent already exists
        existing = store.get_agent_card(request.agent_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent card already exists: {request.agent_id}"
            )
        
        # Create agent card from configuration
        success = store.create_agent_from_config(
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            skills=request.skills,
            base_url=request.base_url,
            provider=request.provider,
            version=request.version
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agent card"
            )
        
        # Retrieve the created card
        card = store.get_agent_card(request.agent_id)
        
        return AgentCardResponse(
            agent_id=request.agent_id,
            card=card
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create agent card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent card: {str(e)}"
        )


@router.put("/{agent_id}", response_model=AgentCardResponse)
async def update_agent_card(agent_id: str, request: UpdateAgentCardRequest):
    """
    Update an existing agent card.
    
    Args:
        agent_id: Unique identifier for the agent
        request: Update request with fields to modify
        
    Returns:
        Updated agent card
    """
    try:
        store = get_agent_card_store()
        
        # Get existing card
        card = store.get_agent_card(agent_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent card not found: {agent_id}"
            )
        
        # Update fields if provided
        if request.name is not None:
            card.name = request.name
        if request.description is not None:
            card.description = request.description
        if request.provider is not None:
            card.provider = request.provider
        if request.version is not None:
            card.version = request.version
        if request.skills is not None:
            # Convert skills
            new_skills = []
            for skill_data in request.skills:
                skill = AgentSkill(
                    id=skill_data.get('id', ''),
                    name=skill_data.get('name', ''),
                    description=skill_data.get('description', ''),
                    tags=skill_data.get('tags', []),
                    examples=skill_data.get('examples', [])
                )
                new_skills.append(skill)
            card.skills = new_skills
        
        # Save updated card
        success = store.save_agent_card(agent_id, card)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update agent card"
            )
        
        return AgentCardResponse(
            agent_id=agent_id,
            card=card
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent card '{agent_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent card: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_card(agent_id: str):
    """
    Delete an agent card.
    
    Args:
        agent_id: Unique identifier for the agent
    """
    try:
        store = get_agent_card_store()
        
        success = store.delete_agent_card(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent card not found: {agent_id}"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent card '{agent_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent card: {str(e)}"
        )


@router.get("/.well-known/combined", response_model=AgentCard)
async def get_combined_agent_card(base_url: str = "http://localhost:8000"):
    """
    Get a combined agent card listing all registered agents.
    
    This is useful for getting an overview of all available agents
    and their capabilities in a single A2A protocol card.
    
    Args:
        base_url: Base URL for the A2A endpoint
        
    Returns:
        Combined agent card
    """
    try:
        store = get_agent_card_store()
        combined_card = store.get_combined_agent_card(base_url)
        
        return combined_card
        
    except Exception as e:
        logger.error(f"Failed to get combined agent card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate combined agent card"
        )
