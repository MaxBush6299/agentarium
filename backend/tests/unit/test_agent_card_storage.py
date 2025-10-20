"""
Tests for Agent Card Storage System

Tests the file-based storage and management of A2A protocol agent cards.
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

from src.a2a.agent_cards import (
    AgentCardStore,
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    get_agent_card_store
)


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def agent_store(temp_storage):
    """Create an AgentCardStore with temporary storage"""
    return AgentCardStore(storage_path=temp_storage)


@pytest.fixture
def sample_agent_card():
    """Create a sample agent card for testing"""
    return AgentCard(
        name="Test Agent",
        description="A test agent for unit tests",
        url="http://localhost:8000/a2a",
        version="1.0.0",
        provider="Test Provider",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
            stateTransitionHistory=False
        ),
        skills=[
            AgentSkill(
                id="test-skill",
                name="Test Skill",
                description="A test skill",
                tags=["test", "demo"],
                examples=["Test query 1", "Test query 2"]
            )
        ]
    )


class TestAgentCardStore:
    """Test AgentCardStore CRUD operations"""
    
    def test_save_agent_card(self, agent_store, sample_agent_card):
        """Test saving an agent card"""
        success = agent_store.save_agent_card("test-agent", sample_agent_card)
        assert success
        
        # Verify file exists
        card_path = agent_store._get_card_path("test-agent")
        assert card_path.exists()
        
        # Verify JSON is valid
        with open(card_path, 'r') as f:
            data = json.load(f)
        assert data["name"] == "Test Agent"
        assert data["metadata"]["agent_id"] == "test-agent"
    
    def test_get_agent_card(self, agent_store, sample_agent_card):
        """Test retrieving an agent card"""
        # Save first
        agent_store.save_agent_card("test-agent", sample_agent_card)
        
        # Retrieve
        card = agent_store.get_agent_card("test-agent")
        assert card is not None
        assert card.name == "Test Agent"
        assert card.description == "A test agent for unit tests"
        assert len(card.skills) == 1
        assert card.skills[0].id == "test-skill"
    
    def test_get_nonexistent_agent_card(self, agent_store):
        """Test retrieving a non-existent agent card"""
        card = agent_store.get_agent_card("nonexistent")
        assert card is None
    
    def test_delete_agent_card(self, agent_store, sample_agent_card):
        """Test deleting an agent card"""
        # Save first
        agent_store.save_agent_card("test-agent", sample_agent_card)
        
        # Delete
        success = agent_store.delete_agent_card("test-agent")
        assert success
        
        # Verify it's gone
        card = agent_store.get_agent_card("test-agent")
        assert card is None
    
    def test_delete_nonexistent_agent_card(self, agent_store):
        """Test deleting a non-existent agent card"""
        success = agent_store.delete_agent_card("nonexistent")
        assert not success
    
    def test_list_agent_ids(self, agent_store, sample_agent_card):
        """Test listing all agent IDs"""
        # Save multiple agents
        agent_store.save_agent_card("agent-1", sample_agent_card)
        agent_store.save_agent_card("agent-2", sample_agent_card)
        agent_store.save_agent_card("agent-3", sample_agent_card)
        
        # List
        agent_ids = agent_store.list_agent_ids()
        assert len(agent_ids) == 3
        assert "agent-1" in agent_ids
        assert "agent-2" in agent_ids
        assert "agent-3" in agent_ids
    
    def test_list_all_cards(self, agent_store, sample_agent_card):
        """Test listing all agent cards"""
        # Save multiple agents
        agent_store.save_agent_card("agent-1", sample_agent_card)
        agent_store.save_agent_card("agent-2", sample_agent_card)
        
        # List all
        all_cards = agent_store.list_all_cards()
        assert len(all_cards) == 2
        assert "agent-1" in all_cards
        assert "agent-2" in all_cards
        assert isinstance(all_cards["agent-1"], AgentCard)
    
    def test_create_agent_from_config(self, agent_store):
        """Test creating an agent card from configuration"""
        success = agent_store.create_agent_from_config(
            agent_id="config-agent",
            name="Config Agent",
            description="Agent created from config",
            skills=[
                {
                    "id": "config-skill",
                    "name": "Config Skill",
                    "description": "A configured skill",
                    "tags": ["config", "test"],
                    "examples": ["Config example"]
                }
            ],
            base_url="http://localhost:8000",
            provider="Config Provider",
            version="2.0.0"
        )
        
        assert success
        
        # Verify it was created
        card = agent_store.get_agent_card("config-agent")
        assert card is not None
        assert card.name == "Config Agent"
        assert card.version == "2.0.0"
        assert card.provider == "Config Provider"
        assert len(card.skills) == 1
        assert card.skills[0].id == "config-skill"


class TestCombinedAgentCard:
    """Test combined agent card generation"""
    
    def test_get_combined_agent_card(self, agent_store, sample_agent_card):
        """Test generating a combined agent card"""
        # Create multiple agents with different skills
        card1 = AgentCard(
            name="Agent 1",
            description="First agent",
            url="http://localhost:8000/a2a",
            version="1.0.0",
            skills=[
                AgentSkill(
                    id="skill-1",
                    name="Skill 1",
                    description="First skill",
                    tags=["tag1"],
                    examples=[]
                )
            ]
        )
        
        card2 = AgentCard(
            name="Agent 2",
            description="Second agent",
            url="http://localhost:8000/a2a",
            version="1.0.0",
            skills=[
                AgentSkill(
                    id="skill-2",
                    name="Skill 2",
                    description="Second skill",
                    tags=["tag2"],
                    examples=[]
                )
            ]
        )
        
        agent_store.save_agent_card("agent-1", card1)
        agent_store.save_agent_card("agent-2", card2)
        
        # Get combined card
        combined = agent_store.get_combined_agent_card("http://localhost:8000")
        
        assert combined is not None
        assert combined.name == "Multi-Agent System"
        assert len(combined.skills) == 2
        assert combined.metadata["agent_count"] == 2
        assert "agent-1" in combined.metadata["agent_ids"]
        assert "agent-2" in combined.metadata["agent_ids"]
    
    def test_combined_card_empty(self, agent_store):
        """Test combined card with no agents"""
        combined = agent_store.get_combined_agent_card("http://localhost:8000")
        
        assert combined is not None
        assert combined.name == "Multi-Agent System"
        assert len(combined.skills) == 0
        assert "No agents currently registered" in combined.description
    
    def test_combined_card_skill_namespacing(self, agent_store):
        """Test that skills are properly namespaced in combined card"""
        card = AgentCard(
            name="Test Agent",
            description="Test",
            url="http://localhost:8000/a2a",
            version="1.0.0",
            skills=[
                AgentSkill(
                    id="my-skill",
                    name="My Skill",
                    description="Test skill",
                    tags=[],
                    examples=[]
                )
            ]
        )
        
        agent_store.save_agent_card("test-agent", card)
        combined = agent_store.get_combined_agent_card("http://localhost:8000")
        
        # Skill should be namespaced with agent ID
        skill_ids = [skill.id for skill in combined.skills]
        assert any("test-agent" in skill_id for skill_id in skill_ids)


class TestAgentCardValidation:
    """Test agent card validation"""
    
    def test_invalid_agent_card(self, agent_store):
        """Test that invalid agent cards are rejected"""
        # Create invalid JSON file
        invalid_path = agent_store._get_card_path("invalid")
        with open(invalid_path, 'w') as f:
            json.dump({"invalid": "data"}, f)
        
        # Should return None for invalid card
        card = agent_store.get_agent_card("invalid")
        assert card is None
    
    def test_malformed_json(self, agent_store):
        """Test handling of malformed JSON"""
        # Create malformed JSON file
        invalid_path = agent_store._get_card_path("malformed")
        with open(invalid_path, 'w') as f:
            f.write("{invalid json}")
        
        # Should return None
        card = agent_store.get_agent_card("malformed")
        assert card is None


class TestGlobalStoreInstance:
    """Test global agent card store singleton"""
    
    def test_get_agent_card_store_singleton(self):
        """Test that get_agent_card_store returns singleton"""
        store1 = get_agent_card_store()
        store2 = get_agent_card_store()
        
        # Should be the same instance
        assert store1 is store2
    
    def test_default_storage_path(self):
        """Test that default storage path is created"""
        store = get_agent_card_store()
        
        # Should have valid storage path
        assert store.storage_path.exists()
        assert store.storage_path.is_dir()


class TestMetadata:
    """Test metadata handling in agent cards"""
    
    def test_metadata_auto_added(self, agent_store, sample_agent_card):
        """Test that metadata is automatically added on save"""
        agent_store.save_agent_card("test-agent", sample_agent_card)
        
        card = agent_store.get_agent_card("test-agent")
        assert card.metadata is not None
        assert "agent_id" in card.metadata
        assert "last_updated" in card.metadata
        assert card.metadata["agent_id"] == "test-agent"
    
    def test_metadata_preserved(self, agent_store, sample_agent_card):
        """Test that custom metadata is preserved"""
        sample_agent_card.metadata = {
            "custom_field": "custom_value",
            "created_by": "test_user"
        }
        
        agent_store.save_agent_card("test-agent", sample_agent_card)
        card = agent_store.get_agent_card("test-agent")
        
        assert card.metadata["custom_field"] == "custom_value"
        assert card.metadata["created_by"] == "test_user"
        # Auto-added fields should also be present
        assert "agent_id" in card.metadata
        assert "last_updated" in card.metadata
