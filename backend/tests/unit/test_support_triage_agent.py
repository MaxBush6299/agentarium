"""Unit tests for the Support Triage Agent."""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Any

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from src.agents.support_triage import SupportTriageAgent, SUPPORT_TRIAGE_SYSTEM_PROMPT
from src.agents.base import DemoBaseAgent


class TestSupportTriageAgentCreation:
    """Tests for Support Triage Agent creation and initialization."""
    
    def test_create_with_defaults(self):
        """Test creating agent with default parameters."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base:
            
            mock_learn.return_value = Mock(name="learn_tool")
            mock_support.return_value = Mock(name="support_tool")
            mock_base.return_value = Mock(spec=DemoBaseAgent)
            
            agent = SupportTriageAgent.create()
            
            assert agent is not None
            assert agent.name == "Support Triage Agent"
            mock_learn.assert_called_once()
            mock_support.assert_called_once()
    
    def test_create_with_custom_model(self):
        """Test creating agent with custom model."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            mock_base.return_value = Mock(spec=DemoBaseAgent)
            
            agent = SupportTriageAgent.create(model="gpt-4")
            
            # Verify base agent was created with custom model
            mock_base.assert_called_once()
            call_kwargs = mock_base.call_args[1]
            assert call_kwargs['model'] == "gpt-4"
    
    def test_create_with_custom_temperature(self):
        """Test creating agent with custom temperature."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            mock_base.return_value = Mock(spec=DemoBaseAgent)
            
            agent = SupportTriageAgent.create(temperature=0.5)
            
            call_kwargs = mock_base.call_args[1]
            assert call_kwargs['temperature'] == 0.5
    
    def test_create_with_custom_max_messages(self):
        """Test creating agent with custom max_messages."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            mock_base.return_value = Mock(spec=DemoBaseAgent)
            
            agent = SupportTriageAgent.create(max_messages=30)
            
            call_kwargs = mock_base.call_args[1]
            assert call_kwargs['max_messages'] == 30
    
    def test_create_initializes_both_tools(self):
        """Test that creation initializes both Microsoft Learn and Support Triage tools."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base:
            
            learn_tool = Mock(name="learn_tool")
            support_tool = Mock(name="support_tool")
            
            mock_learn.return_value = learn_tool
            mock_support.return_value = support_tool
            mock_base.return_value = Mock(spec=DemoBaseAgent)
            
            agent = SupportTriageAgent.create()
            
            # Verify both tools were created
            mock_learn.assert_called_once()
            mock_support.assert_called_once()
            
            # Verify tools were passed to base agent
            call_kwargs = mock_base.call_args[1]
            assert learn_tool in call_kwargs['tools']
            assert support_tool in call_kwargs['tools']
            assert len(call_kwargs['tools']) == 2
    
    def test_create_uses_correct_system_prompt(self):
        """Test that agent uses the correct system prompt."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            mock_base.return_value = Mock(spec=DemoBaseAgent)
            
            agent = SupportTriageAgent.create()
            
            call_kwargs = mock_base.call_args[1]
            assert call_kwargs['instructions'] == SUPPORT_TRIAGE_SYSTEM_PROMPT
            assert "Microsoft product support triage specialist" in call_kwargs['instructions']
    
    def test_create_handles_tool_creation_failure(self):
        """Test that agent creation handles tool creation failures."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn:
            mock_learn.side_effect = Exception("MCP server unavailable")
            
            with pytest.raises(ConnectionError, match="Failed to initialize Support Triage Agent tools"):
                SupportTriageAgent.create()
    
    def test_create_handles_base_agent_creation_failure(self):
        """Test that agent creation handles base agent failures."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            mock_base.side_effect = Exception("Azure OpenAI unavailable")
            
            with pytest.raises(ValueError, match="Failed to create Support Triage Agent"):
                SupportTriageAgent.create()


class TestSupportTriageAgentProperties:
    """Tests for Support Triage Agent properties."""
    
    def test_name_property(self):
        """Test that agent has correct name."""
        mock_base = Mock(spec=DemoBaseAgent)
        agent = SupportTriageAgent(mock_base)
        
        assert agent.name == "Support Triage Agent"
    
    def test_id_property_delegates_to_base(self):
        """Test that id property delegates to base agent."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_base.id = "test-agent-id"
        
        agent = SupportTriageAgent(mock_base)
        
        assert agent.id == "test-agent-id"
    
    def test_display_name_property_delegates_to_base(self):
        """Test that display_name property delegates to base agent."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_base.display_name = "Support Triage Agent"
        
        agent = SupportTriageAgent(mock_base)
        
        assert agent.display_name == "Support Triage Agent"


class TestSupportTriageAgentThreadManagement:
    """Tests for thread management methods."""
    
    def test_get_new_thread(self):
        """Test getting a new conversation thread."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_thread = Mock(name="thread")
        mock_base.get_new_thread.return_value = mock_thread
        
        agent = SupportTriageAgent(mock_base)
        thread = agent.get_new_thread()
        
        assert thread == mock_thread
        mock_base.get_new_thread.assert_called_once_with()
    
    def test_get_new_thread_with_kwargs(self):
        """Test getting a new thread with custom kwargs."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_thread = Mock(name="thread")
        mock_base.get_new_thread.return_value = mock_thread
        
        agent = SupportTriageAgent(mock_base)
        thread = agent.get_new_thread(metadata={"user_id": "123"})
        
        assert thread == mock_thread
        mock_base.get_new_thread.assert_called_once_with(metadata={"user_id": "123"})
    
    @pytest.mark.asyncio
    async def test_serialize_thread(self):
        """Test serializing a thread."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_thread = Mock(name="thread")
        expected_dict = {"id": "thread-123", "messages": []}
        mock_base.serialize_thread = AsyncMock(return_value=expected_dict)
        
        agent = SupportTriageAgent(mock_base)
        result = await agent.serialize_thread(mock_thread)
        
        assert result == expected_dict
        mock_base.serialize_thread.assert_called_once_with(mock_thread)
    
    @pytest.mark.asyncio
    async def test_deserialize_thread(self):
        """Test deserializing a thread."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_thread = Mock(name="thread")
        thread_dict = {"id": "thread-123", "messages": []}
        mock_base.deserialize_thread = AsyncMock(return_value=mock_thread)
        
        agent = SupportTriageAgent(mock_base)
        result = await agent.deserialize_thread(thread_dict)
        
        assert result == mock_thread
        mock_base.deserialize_thread.assert_called_once_with(thread_dict)


class TestSupportTriageAgentRun:
    """Tests for agent run methods."""
    
    @pytest.mark.asyncio
    async def test_run_without_thread(self):
        """Test running agent without existing thread."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_response = Mock(messages=[Mock(content="Response content")])
        mock_base.run = AsyncMock(return_value=mock_response)
        
        agent = SupportTriageAgent(mock_base)
        response = await agent.run("Test query")
        
        assert response == mock_response
        mock_base.run.assert_called_once_with("Test query", thread=None)
    
    @pytest.mark.asyncio
    async def test_run_with_thread(self):
        """Test running agent with existing thread."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_thread = Mock(name="thread")
        mock_response = Mock(messages=[Mock(content="Response content")])
        mock_base.run = AsyncMock(return_value=mock_response)
        
        agent = SupportTriageAgent(mock_base)
        response = await agent.run("Test query", thread=mock_thread)
        
        assert response == mock_response
        mock_base.run.assert_called_once_with("Test query", thread=mock_thread)
    
    @pytest.mark.asyncio
    async def test_run_with_kwargs(self):
        """Test running agent with additional kwargs."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_response = Mock(messages=[Mock(content="Response content")])
        mock_base.run = AsyncMock(return_value=mock_response)
        
        agent = SupportTriageAgent(mock_base)
        response = await agent.run("Test query", max_tokens=1000, temperature=0.5)
        
        assert response == mock_response
        mock_base.run.assert_called_once_with(
            "Test query",
            thread=None,
            max_tokens=1000,
            temperature=0.5
        )


class TestSupportTriageAgentRunStream:
    """Tests for agent streaming methods."""
    
    @pytest.mark.asyncio
    async def test_run_stream_yields_events(self):
        """Test that run_stream yields events from base agent."""
        mock_base = Mock(spec=DemoBaseAgent)
        
        # Create async generator for mock events
        async def mock_stream(*args, **kwargs):
            yield Mock(content="Event 1")
            yield Mock(content="Event 2")
            yield Mock(content="Event 3")
        
        mock_base.run_stream = mock_stream
        
        agent = SupportTriageAgent(mock_base)
        events = []
        
        async for event in agent.run_stream("Test query"):
            events.append(event)
        
        assert len(events) == 3
        assert events[0].content == "Event 1"
        assert events[1].content == "Event 2"
        assert events[2].content == "Event 3"
    
    @pytest.mark.asyncio
    async def test_run_stream_with_thread(self):
        """Test streaming with existing thread."""
        mock_base = Mock(spec=DemoBaseAgent)
        mock_thread = Mock(name="thread")
        
        async def mock_stream(*args, **kwargs):
            yield Mock(content="Event")
        
        mock_base.run_stream = mock_stream
        
        agent = SupportTriageAgent(mock_base)
        events = []
        
        async for event in agent.run_stream("Test query", thread=mock_thread):
            events.append(event)
        
        assert len(events) == 1


class TestSupportTriageAgentSystemPrompt:
    """Tests for system prompt content."""
    
    def test_system_prompt_mentions_responsibilities(self):
        """Test that system prompt includes key responsibilities."""
        assert "analyze support tickets" in SUPPORT_TRIAGE_SYSTEM_PROMPT.lower()
        assert "microsoft learn" in SUPPORT_TRIAGE_SYSTEM_PROMPT.lower()
        assert "similar" in SUPPORT_TRIAGE_SYSTEM_PROMPT.lower()
        assert "recommendations" in SUPPORT_TRIAGE_SYSTEM_PROMPT.lower()
    
    def test_system_prompt_mentions_tools(self):
        """Test that system prompt mentions available tools."""
        assert "Microsoft Learn MCP" in SUPPORT_TRIAGE_SYSTEM_PROMPT
        assert "Support Triage API" in SUPPORT_TRIAGE_SYSTEM_PROMPT
    
    def test_system_prompt_includes_guidance(self):
        """Test that system prompt includes response guidance."""
        assert "ground your responses" in SUPPORT_TRIAGE_SYSTEM_PROMPT.lower()
        assert "specific" in SUPPORT_TRIAGE_SYSTEM_PROMPT.lower()
        assert "step-by-step" in SUPPORT_TRIAGE_SYSTEM_PROMPT.lower()


class TestSupportTriageAgentIntegration:
    """Integration tests for Support Triage Agent workflows."""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test complete conversation flow with thread management."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base_class:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            
            # Create mock base agent instance
            mock_base = Mock(spec=DemoBaseAgent)
            mock_thread = Mock(name="thread")
            mock_response1 = Mock(messages=[Mock(content="Response 1")])
            mock_response2 = Mock(messages=[Mock(content="Response 2")])
            
            mock_base.get_new_thread.return_value = mock_thread
            mock_base.run = AsyncMock(side_effect=[mock_response1, mock_response2])
            mock_base_class.return_value = mock_base
            
            # Create agent
            agent = SupportTriageAgent.create()
            
            # Start conversation
            thread = agent.get_new_thread()
            
            # First message
            response1 = await agent.run("First query", thread=thread)
            assert response1 == mock_response1
            
            # Second message (continuation)
            response2 = await agent.run("Follow-up query", thread=thread)
            assert response2 == mock_response2
            
            # Verify thread was reused
            assert mock_base.run.call_count == 2
            assert mock_base.run.call_args_list[0][1]['thread'] == thread
            assert mock_base.run.call_args_list[1][1]['thread'] == thread
    
    @pytest.mark.asyncio
    async def test_thread_persistence_workflow(self):
        """Test thread serialization and deserialization workflow."""
        with patch('src.agents.support_triage.get_microsoft_learn_tool') as mock_learn, \
             patch('src.agents.support_triage.get_support_triage_tool') as mock_support, \
             patch('src.agents.support_triage.DemoBaseAgent') as mock_base_class:
            
            mock_learn.return_value = Mock()
            mock_support.return_value = Mock()
            
            # Create mock base agent
            mock_base = Mock(spec=DemoBaseAgent)
            mock_thread = Mock(name="thread")
            thread_dict = {"id": "thread-123", "messages": []}
            
            mock_base.get_new_thread.return_value = mock_thread
            mock_base.serialize_thread = AsyncMock(return_value=thread_dict)
            mock_base.deserialize_thread = AsyncMock(return_value=mock_thread)
            mock_base_class.return_value = mock_base
            
            # Create agent
            agent = SupportTriageAgent.create()
            
            # Create thread
            thread = agent.get_new_thread()
            
            # Serialize thread (for saving to DB)
            serialized = await agent.serialize_thread(thread)
            assert serialized == thread_dict
            
            # Deserialize thread (for loading from DB)
            restored_thread = await agent.deserialize_thread(serialized)
            assert restored_thread == mock_thread
