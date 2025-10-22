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

# Import for auto-card generation from agent factory metadata
from src.persistence.models import AgentMetadata


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
            AgentCard object or None if not found or invalid
        """
        try:
            card_path = self._get_card_path(agent_id)
            
            if not card_path.exists():
                logger.warning(f"Agent card not found for '{agent_id}'")
                return None
            
            with open(card_path, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            # Skip legacy card formats (non-A2A compliant)
            # Legacy cards have "capabilities" and "skills" as simple lists/dicts
            # A2A cards have AgentSkill objects and AgentCapabilities
            if not self._is_valid_a2a_card(card_data):
                logger.debug(f"Card for '{agent_id}' is not A2A compliant, skipping")
                return None
            
            card = AgentCard(**card_data)
            logger.debug(f"Loaded agent card for '{agent_id}'")
            return card
            
        except ValidationError as e:
            logger.warning(f"Invalid agent card format for '{agent_id}' (likely legacy format): {str(e)[:100]}...")
            return None
        except Exception as e:
            logger.error(f"Failed to load agent card for '{agent_id}': {e}")
            return None
    
    def _is_valid_a2a_card(self, card_data: dict) -> bool:
        """
        Check if card data is A2A protocol compliant.
        
        A2A cards must have:
        - name (str)
        - description (str)
        - url (str)
        - skills (list of AgentSkill objects or dicts with id, name, description)
        
        Args:
            card_data: Card data dictionary
            
        Returns:
            True if card is A2A compliant, False otherwise
        """
        # Check required A2A fields
        if not isinstance(card_data.get('name'), str):
            return False
        if not isinstance(card_data.get('description'), str):
            return False
        if not isinstance(card_data.get('url'), str):
            return False
        
        # Check skills format - should be a list, not a dict
        skills = card_data.get('skills', [])
        if not isinstance(skills, list):
            logger.debug(f"Skills is not a list: {type(skills)}")
            return False
        
        if skills and isinstance(skills[0], dict):
            # Check first skill has required A2A fields
            skill = skills[0]
            if not all(k in skill for k in ['id', 'name', 'description']):
                logger.debug(f"Skill missing required fields: {skill.keys()}")
                return False
        
        return True
    
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
        
        Includes both:
        1. Manual JSON files stored in the file system
        2. Auto-generated cards from backend agent metadata (Cosmos DB)
        
        Returns:
            Dictionary mapping agent_id to AgentCard
        """
        cards = {}
        
        # Load manually created JSON cards from file storage
        for agent_id in self.list_agent_ids():
            card = self.get_agent_card(agent_id)
            if card:
                cards[agent_id] = card
        
        # Load and auto-generate cards from backend agent metadata
        try:
            from src.persistence.agents import get_agent_repository
            repo = get_agent_repository()
            
            # Get all agents from Cosmos DB
            all_agents = repo.list()
            logger.info(f"Found {len(all_agents)} agents in database for auto-card generation")
            
            for agent_metadata in all_agents:
                # Skip if we already have a manual card for this agent
                if agent_metadata.id in cards:
                    logger.debug(f"Using manual card for '{agent_metadata.id}', skipping auto-generation")
                    continue
                
                # Auto-generate card from metadata
                auto_card = self.generate_card_from_agent_metadata(
                    agent_metadata,
                    base_url="http://localhost:8000"  # Could be parameterized
                )
                cards[agent_metadata.id] = auto_card
                logger.debug(f"Auto-generated card for '{agent_metadata.id}'")
                
        except Exception as e:
            logger.warning(f"Failed to load agents from repository for auto-card generation: {e}")
            # Don't fail - just use file-based cards only
        
        return cards
    
    def get_combined_agent_card(self, base_url: str) -> AgentCard:
        """
        Generate a combined agent card that lists all registered agents.
        
        This is useful for the /.well-known/agent.json endpoint to expose
        all available agents as skills in a single card for agent-to-agent discovery.
        
        Each agent becomes a skill in the combined card, with:
        - name: agent's display name
        - description: agent's description
        - tags: agent's user-defined capabilities + tool types
        - id: agent_id from metadata
        
        Args:
            base_url: Base URL for the A2A endpoint (e.g., http://localhost:8000)
            
        Returns:
            Combined AgentCard with all agents as skills
        """
        all_cards = self.list_all_cards()
        
        if not all_cards:
            logger.warning("No agent cards found, returning empty combined card")
            return AgentCard(
                name="Multi-Agent System",
                description="No agents currently registered",
                url=base_url,
                skills=[]
            )
        
        # Collect all agents as skills for discovery
        all_skills = []
        
        for agent_id, card in all_cards.items():
            # Create a skill entry for each agent
            # Tags include: user-defined capabilities + tool types
            tags = []
            
            # Add user-defined capabilities from metadata
            if card.metadata and "capabilities" in card.metadata:
                caps = card.metadata.get("capabilities", [])
                if isinstance(caps, list):
                    tags.extend(caps)
            
            # Add tool types as tags
            for skill in card.skills:
                tags.extend(skill.tags)
            
            # Remove duplicates but preserve order
            tags = list(dict.fromkeys(tags))
            
            # Create skill representing this agent
            agent_skill = AgentSkill(
                id=agent_id,
                name=card.name,
                description=card.description or f"Agent: {agent_id}",
                tags=tags,  # Now includes both user capabilities and tool types
                examples=[]
            )
            all_skills.append(agent_skill)
        
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
        
        logger.info(f"Generated combined card with {len(all_skills)} agent skills")
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
    
    def generate_card_from_agent_metadata(
        self,
        agent_metadata: AgentMetadata,
        base_url: str
    ) -> AgentCard:
        """
        Automatically generate an A2A agent card from backend agent metadata.
        
        This method bridges the gap between internal agent configuration (AgentMetadata)
        and the A2A protocol discovery mechanism. It eliminates the need for manual
        card creation - agents are automatically discoverable based on their metadata.
        
        Mapping:
        - agent_metadata.tools[] → AgentCard.skills[]
        - agent_metadata.capabilities[] → AgentCard.skills[].tags
        - agent_metadata.name → AgentCard.name
        - agent_metadata.description → AgentCard.description
        
        Args:
            agent_metadata: AgentMetadata from Cosmos DB
            base_url: Base URL for the A2A endpoint (e.g., http://localhost:8000)
            
        Returns:
            Generated AgentCard ready for A2A protocol discovery
        """
        logger.info(f"Auto-generating A2A card for agent '{agent_metadata.id}'")
        
        # Build skills from agent's tools
        # Each tool becomes a skill in the A2A card
        skills = []
        if agent_metadata.tools:
            for idx, tool in enumerate(agent_metadata.tools):
                skill = AgentSkill(
                    id=tool.name,  # Use tool name as skill id
                    name=tool.name,  # Tool name becomes skill name
                    description=f"Tool: {tool.type}",  # Tool type as description
                    tags=[tool.type],  # Tag with tool type (mcp, openapi, etc)
                    examples=[]
                )
                skills.append(skill)
        
        # Create A2A card from metadata
        card = AgentCard(
            name=agent_metadata.name,
            description=agent_metadata.description or f"Agent: {agent_metadata.id}",
            url=f"{base_url}/api/agents/{agent_metadata.id}",
            version=agent_metadata.version or "1.0.0",
            provider=None,  # Could be extracted from config if available
            capabilities=AgentCapabilities(
                streaming=False,  # Could be determined from agent config
                pushNotifications=False,
                stateTransitionHistory=False
            ),
            skills=skills,
            metadata={
                "source": "auto-generated",
                "from_metadata": True,
                "capabilities": agent_metadata.capabilities,  # Store user-defined capabilities
                "model": agent_metadata.model,
                "status": agent_metadata.status.value if hasattr(agent_metadata.status, 'value') else str(agent_metadata.status),
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.debug(f"Generated card for '{agent_metadata.id}' with {len(skills)} skills")
        return card


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
