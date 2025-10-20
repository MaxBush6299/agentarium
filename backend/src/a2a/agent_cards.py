"""
Agent Card Storage and Management

This module provides persistent storage for A2A Protocol agent cards.
Agent cards are stored as JSON files and can be dynamically created,
updated, and retrieved for agent discovery.

Features:
- File-based storage for agent cards
- CRUD operations for agent cards
- Automatic discovery of all registered agents
- Support for dynamic agent registration from frontend
- Validation against A2A protocol requirements
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Card Models (per A2A spec Section 5)
# ============================================================================

class AgentSkill(BaseModel):
    """Agent skill definition per A2A spec Section 5.4"""
    id: str
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class AgentCapabilities(BaseModel):
    """Agent capabilities per A2A spec Section 5.5"""
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class AgentCard(BaseModel):
    """A2A Agent Card per spec Section 5"""
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    url: str
    preferredTransport: str = "JSONRPC"
    version: str = "1.0.0"
    provider: Optional[str] = None
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    skills: List[AgentSkill] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Agent Card Store
# ============================================================================

class AgentCardStore:
    """
    File-based storage for agent cards.
    
    Agent cards are stored as JSON files in a designated directory.
    Each agent has a unique ID that maps to a filename (agent_id.json).
    
    The store provides:
    - Create/Update/Delete operations
    - List all registered agents
    - Get specific agent card by ID
    - Generate combined agent card for discovery endpoint
    - Validation of agent card structure
    
    Directory structure:
        agent-cards/
            support-triage.json
            ops-assistant.json
            sql-query.json
            ...
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the agent card store.
        
        Args:
            storage_path: Directory path for storing agent cards.
                         Defaults to ./data/agent-cards/
        """
        if storage_path is None:
            # Default to data/agent-cards relative to project root
            project_root = Path(__file__).parent.parent.parent
            storage_path = project_root / "data" / "agent-cards"
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"AgentCardStore initialized at: {self.storage_path}")
    
    def _get_card_path(self, agent_id: str) -> Path:
        """Get the file path for an agent card."""
        return self.storage_path / f"{agent_id}.json"
    
    def save_agent_card(self, agent_id: str, card: AgentCard) -> bool:
        """
        Save an agent card to storage.
        
        Args:
            agent_id: Unique identifier for the agent
            card: Agent card object
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            card_path = self._get_card_path(agent_id)
            
            # Add metadata for tracking
            if card.metadata is None:
                card.metadata = {}
            card.metadata["agent_id"] = agent_id
            card.metadata["last_updated"] = datetime.utcnow().isoformat()
            
            # Write to file with pretty formatting
            with open(card_path, 'w', encoding='utf-8') as f:
                json.dump(card.model_dump(exclude_none=True), f, indent=2)
            
            logger.info(f"Saved agent card for '{agent_id}' to {card_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent card for '{agent_id}': {e}")
            return False
    
    def get_agent_card(self, agent_id: str) -> Optional[AgentCard]:
        """
        Retrieve an agent card from storage.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            AgentCard object or None if not found
        """
        try:
            card_path = self._get_card_path(agent_id)
            
            if not card_path.exists():
                logger.warning(f"Agent card not found for '{agent_id}'")
                return None
            
            with open(card_path, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            card = AgentCard(**card_data)
            logger.debug(f"Loaded agent card for '{agent_id}'")
            return card
            
        except ValidationError as e:
            logger.error(f"Invalid agent card format for '{agent_id}': {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load agent card for '{agent_id}': {e}")
            return None
    
    def delete_agent_card(self, agent_id: str) -> bool:
        """
        Delete an agent card from storage.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            card_path = self._get_card_path(agent_id)
            
            if not card_path.exists():
                logger.warning(f"Agent card not found for deletion: '{agent_id}'")
                return False
            
            card_path.unlink()
            logger.info(f"Deleted agent card for '{agent_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete agent card for '{agent_id}': {e}")
            return False
    
    def list_agent_ids(self) -> List[str]:
        """
        List all registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        try:
            agent_ids = [
                f.stem for f in self.storage_path.glob("*.json")
            ]
            logger.debug(f"Found {len(agent_ids)} agent cards")
            return sorted(agent_ids)
            
        except Exception as e:
            logger.error(f"Failed to list agent cards: {e}")
            return []
    
    def list_all_cards(self) -> Dict[str, AgentCard]:
        """
        Load all agent cards from storage.
        
        Returns:
            Dictionary mapping agent_id to AgentCard
        """
        cards = {}
        for agent_id in self.list_agent_ids():
            card = self.get_agent_card(agent_id)
            if card:
                cards[agent_id] = card
        return cards
    
    def get_combined_agent_card(self, base_url: str) -> AgentCard:
        """
        Generate a combined agent card that lists all registered agents.
        
        This is useful for the /.well-known/agent.json endpoint to expose
        all available agents as skills in a single card.
        
        Args:
            base_url: Base URL for the A2A endpoint (e.g., http://localhost:8000/a2a)
            
        Returns:
            Combined AgentCard with all agents as skills
        """
        all_cards = self.list_all_cards()
        
        if not all_cards:
            logger.warning("No agent cards found, returning empty card")
            return AgentCard(
                name="Multi-Agent System",
                description="No agents currently registered",
                url=base_url,
                skills=[]
            )
        
        # Collect all skills from all agents
        all_skills = []
        for agent_id, card in all_cards.items():
            for skill in card.skills:
                # Add agent_id to skill metadata for routing
                skill_data = skill.model_dump()
                if agent_id not in skill_data.get('id', ''):
                    skill_data['id'] = f"{agent_id}-{skill_data['id']}"
                all_skills.append(AgentSkill(**skill_data))
        
        # Create combined card
        combined_card = AgentCard(
            name="Multi-Agent System",
            description=f"Unified agent system with {len(all_cards)} specialized agents",
            url=base_url,
            version="1.0.0",
            provider="Multi-Agent Demo",
            capabilities=AgentCapabilities(
                streaming=False,
                pushNotifications=False,
                stateTransitionHistory=False
            ),
            skills=all_skills,
            metadata={
                "agent_count": len(all_cards),
                "agent_ids": list(all_cards.keys()),
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
        return combined_card
    
    def create_agent_from_config(
        self,
        agent_id: str,
        name: str,
        description: str,
        skills: List[Dict[str, Any]],
        base_url: str,
        provider: Optional[str] = None,
        version: str = "1.0.0"
    ) -> bool:
        """
        Create a new agent card from configuration parameters.
        
        This is useful when dynamically creating agents from the frontend.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Agent display name
            description: Agent description
            skills: List of skill definitions (id, name, description, tags, examples)
            base_url: Base URL for A2A endpoint
            provider: Optional provider name
            version: Agent version
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Build skills
            agent_skills = []
            for skill_data in skills:
                skill = AgentSkill(
                    id=skill_data.get('id', f"{agent_id}-skill"),
                    name=skill_data.get('name', ''),
                    description=skill_data.get('description', ''),
                    tags=skill_data.get('tags', []),
                    examples=skill_data.get('examples', [])
                )
                agent_skills.append(skill)
            
            # Create agent card
            card = AgentCard(
                name=name,
                description=description,
                url=f"{base_url}/{agent_id}",
                version=version,
                provider=provider,
                skills=agent_skills,
                metadata={
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "frontend"
                }
            )
            
            return self.save_agent_card(agent_id, card)
            
        except Exception as e:
            logger.error(f"Failed to create agent card from config: {e}")
            return False


# ============================================================================
# Global Agent Card Store Instance
# ============================================================================

# Singleton instance
_agent_card_store: Optional[AgentCardStore] = None


def get_agent_card_store(storage_path: Optional[Path] = None) -> AgentCardStore:
    """
    Get the global agent card store instance.
    
    Args:
        storage_path: Optional custom storage path
        
    Returns:
        AgentCardStore instance
    """
    global _agent_card_store
    
    if _agent_card_store is None:
        _agent_card_store = AgentCardStore(storage_path)
    
    return _agent_card_store
