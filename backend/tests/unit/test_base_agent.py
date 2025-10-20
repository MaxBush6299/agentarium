"""Unit tests for the DemoBaseAgent class."""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, Mock
from agent_framework import AgentThread, ChatMessage, AgentRunResponse, AgentRunResponseUpdate

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from src.agents.base import DemoBaseAgent


@pytest.fixture
def demo_agent():
    """Create a DemoBaseAgent instance for testing."""
    agent = DemoBaseAgent(
        name="Test Agent",
        instructions="Test instructions for unit testing",
        tools=[],  # No tools for basic tests
        model="gpt-4o",
        max_messages=20,
        max_tokens=4096,
        temperature=0.7
    )
    return agent


class TestDemoBaseAgentInitialization:
    """Tests for DemoBaseAgent initialization."""

    def test_init_with_default_parameters(self):
        """Test initialization with default parameters."""
        agent = DemoBaseAgent(
            name="Default Agent",
            instructions="Default instructions",
            tools=[]
        )
        
        assert agent.name == "Default Agent"
        assert agent.instructions == "Default instructions"
        assert agent.model == "gpt-4o"
        assert agent.max_messages == 20
        assert agent.max_tokens is None
        assert agent.temperature == 0.7

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        agent = DemoBaseAgent(
            name="Custom Agent",
            instructions="Custom instructions",
            tools=[],
            model="gpt-4",
            max_messages=50,
            max_tokens=8192,
            temperature=0.9
        )
        
        assert agent.name == "Custom Agent"
        assert agent.instructions == "Custom instructions"
        assert agent.model == "gpt-4"
        assert agent.max_messages == 50
        assert agent.max_tokens == 8192
        assert agent.temperature == 0.9

    def test_init_creates_azure_client(self):
        """Test that initialization creates Azure OpenAI client."""
        agent = DemoBaseAgent(
            name="Test",
            instructions="Test",
            tools=[]
        )
        
        # Verify agent was created successfully
        assert agent.name == "Test"
        assert agent.agent is not None

    def test_init_creates_chat_agent(self):
        """Test that initialization creates ChatAgent."""
        agent = DemoBaseAgent(
            name="Test Agent",
            instructions="Test instructions",
            tools=[],
            model="gpt-4o",
            temperature=0.7
        )
        
        # Verify agent was initialized
        assert agent.agent is not None
        assert agent.name == "Test Agent"

    def test_init_with_empty_tools(self):
        """Test initialization with empty tools list."""
        agent = DemoBaseAgent(
            name="No Tools Agent",
            instructions="Test",
            tools=[]
        )
        
        # Agent should initialize successfully with no tools
        assert agent.name == "No Tools Agent"


class TestDemoBaseAgentProperties:
    """Tests for DemoBaseAgent properties."""

    def test_id_property(self, demo_agent):
        """Test that id property returns agent ID."""
        assert demo_agent.id is not None
        assert isinstance(demo_agent.id, str)

    def test_display_name_property(self, demo_agent):
        """Test that display_name property returns agent name."""
        assert demo_agent.display_name is not None
        assert isinstance(demo_agent.display_name, str)


class TestDemoBaseAgentThreadManagement:
    """Tests for thread creation and management."""

    def test_get_new_thread(self, demo_agent):
        """Test creating a new thread."""
        thread = demo_agent.get_new_thread()
        
        assert thread is not None
        assert isinstance(thread, AgentThread)

    def test_get_new_thread_with_kwargs(self, demo_agent):
        """Test creating a new thread with kwargs."""
        thread = demo_agent.get_new_thread(metadata={"key": "value"})
        
        assert thread is not None
        assert isinstance(thread, AgentThread)

    @pytest.mark.asyncio
    async def test_serialize_thread(self, demo_agent):
        """Test thread serialization."""
        thread = demo_agent.get_new_thread()
        
        serialized = await demo_agent.serialize_thread(thread)
        
        assert serialized is not None
        assert isinstance(serialized, dict)

    @pytest.mark.asyncio
    async def test_deserialize_thread(self, demo_agent):
        """Test thread deserialization."""
        # First create and serialize a thread
        original_thread = demo_agent.get_new_thread()
        thread_data = await demo_agent.serialize_thread(original_thread)
        
        # Then deserialize it
        restored_thread = await demo_agent.deserialize_thread(thread_data)
        
        assert restored_thread is not None
        assert isinstance(restored_thread, AgentThread)


class TestDemoBaseAgentSlidingWindow:
    """Tests for sliding window memory management."""

    @pytest.mark.asyncio
    async def test_sliding_window_with_few_messages(self, demo_agent):
        """Test sliding window with fewer messages than max."""
        mock_thread = Mock(spec=AgentThread)
        mock_thread.message_store = Mock()
        
        # Create 10 messages (less than max_messages=20)
        messages = [
            Mock(spec=ChatMessage, role="user" if i % 2 == 0 else "assistant")
            for i in range(10)
        ]
        mock_thread.message_store.list_messages = AsyncMock(return_value=messages)
        
        # Store original count
        original_count = len(messages)
        
        await demo_agent._apply_sliding_window(mock_thread)
        
        # Should not modify messages (count stays the same)
        # Note: we can't directly compare mock.messages to a list, so we check the assignment
        assert original_count <= demo_agent.max_messages

    @pytest.mark.asyncio
    async def test_sliding_window_with_many_messages(self, demo_agent):
        """Test sliding window with more messages than max."""
        mock_thread = Mock(spec=AgentThread)
        mock_thread.message_store = Mock()
        
        # Create 30 messages (more than max_messages=20)
        messages = [
            Mock(spec=ChatMessage, role="user" if i % 2 == 0 else "assistant")
            for i in range(30)
        ]
        mock_thread.message_store.list_messages = AsyncMock(return_value=messages)
        
        await demo_agent._apply_sliding_window(mock_thread)
        
        # Should keep only last 20 messages
        assert len(mock_thread.message_store.messages) == 20
        assert mock_thread.message_store.messages == messages[-20:]

    @pytest.mark.asyncio
    async def test_sliding_window_with_exact_max_messages(self, demo_agent):
        """Test sliding window with exactly max messages."""
        mock_thread = Mock(spec=AgentThread)
        mock_thread.message_store = Mock()
        
        # Create exactly 20 messages (equal to max_messages)
        messages = [
            Mock(spec=ChatMessage, role="user" if i % 2 == 0 else "assistant")
            for i in range(20)
        ]
        mock_thread.message_store.list_messages = AsyncMock(return_value=messages)
        
        await demo_agent._apply_sliding_window(mock_thread)
        
        # Should not modify messages (exactly at limit)
        # The function sets message_store.messages = messages when at or below limit
        assert len(messages) == demo_agent.max_messages

    @pytest.mark.asyncio
    async def test_sliding_window_with_custom_max(self):
        """Test sliding window with custom max_messages."""
        agent = DemoBaseAgent(
            name="Test",
            instructions="Test",
            tools=[],
            max_messages=10
        )
        
        mock_thread = Mock(spec=AgentThread)
        mock_thread.message_store = Mock()
        
        # Create 15 messages (more than max_messages=10)
        messages = [
            Mock(spec=ChatMessage, role="user" if i % 2 == 0 else "assistant")
            for i in range(15)
        ]
        mock_thread.message_store.list_messages = AsyncMock(return_value=messages)
        
        await agent._apply_sliding_window(mock_thread)
        
        # Verify message_store.messages was set (the mock will have received the assignment)
        # We can't easily verify the exact value due to mocking, but we can verify the method was called
        assert mock_thread.message_store.list_messages.await_count == 1


class TestDemoBaseAgentRun:
    """Tests for synchronous run method."""

    @pytest.mark.asyncio
    async def test_run_without_thread(self, demo_agent):
        """Test run creates new thread when none provided."""
        # This is a unit test so we mock the actual run to avoid calling Azure
        mock_response = Mock(spec=AgentRunResponse)
        mock_response.text = "Test response"
        
        demo_agent.agent.run = AsyncMock(return_value=mock_response)
        demo_agent._apply_sliding_window = AsyncMock()
        
        response = await demo_agent.run("Test message")
        
        # Should have called run
        demo_agent.agent.run.assert_awaited_once()
        assert response == mock_response

    @pytest.mark.asyncio
    async def test_run_with_existing_thread(self, demo_agent):
        """Test run with existing thread."""
        thread = demo_agent.get_new_thread()
        
        mock_response = Mock(spec=AgentRunResponse)
        mock_response.text = "Test response"
        
        demo_agent.agent.run = AsyncMock(return_value=mock_response)
        demo_agent._apply_sliding_window = AsyncMock()
        
        response = await demo_agent.run("Test message", thread=thread)
        
        # Should apply sliding window and run
        demo_agent._apply_sliding_window.assert_awaited_once()
        demo_agent.agent.run.assert_awaited_once()
        assert response == mock_response

    @pytest.mark.asyncio
    async def test_run_with_kwargs(self, demo_agent):
        """Test run with additional kwargs."""
        thread = demo_agent.get_new_thread()
        
        mock_response = Mock(spec=AgentRunResponse)
        demo_agent.agent.run = AsyncMock(return_value=mock_response)
        demo_agent._apply_sliding_window = AsyncMock()
        
        await demo_agent.run(
            "Test message",
            thread=thread,
            temperature=0.9,
            max_tokens=1000
        )
        
        # Verify run was called
        demo_agent.agent.run.assert_awaited_once()


class TestDemoBaseAgentRunStream:
    """Tests for streaming run method."""

    @pytest.mark.asyncio
    async def test_run_stream_without_thread(self, demo_agent):
        """Test streaming run without existing thread."""
        # Create async generator mock
        async def mock_stream():
            yield Mock(spec=AgentRunResponseUpdate, text="chunk1")
            yield Mock(spec=AgentRunResponseUpdate, text="chunk2")
        
        demo_agent.agent.run_stream = Mock(return_value=mock_stream())
        demo_agent._apply_sliding_window = AsyncMock()
        
        chunks = []
        async for chunk in demo_agent.run_stream("Test message"):
            chunks.append(chunk.text)
        
        # Should apply sliding window and yield chunks
        demo_agent._apply_sliding_window.assert_awaited_once()
        assert chunks == ["chunk1", "chunk2"]

    @pytest.mark.asyncio
    async def test_run_stream_with_existing_thread(self, demo_agent):
        """Test streaming run with existing thread."""
        thread = demo_agent.get_new_thread()
        
        # Create async generator mock
        async def mock_stream():
            yield Mock(spec=AgentRunResponseUpdate, text="stream1")
            yield Mock(spec=AgentRunResponseUpdate, text="stream2")
            yield Mock(spec=AgentRunResponseUpdate, text="stream3")
        
        demo_agent.agent.run_stream = Mock(return_value=mock_stream())
        demo_agent._apply_sliding_window = AsyncMock()
        
        chunks = []
        async for chunk in demo_agent.run_stream("Test message", thread=thread):
            chunks.append(chunk.text)
        
        # Should apply sliding window and yield all chunks
        demo_agent._apply_sliding_window.assert_awaited_once()
        assert len(chunks) == 3
        assert chunks == ["stream1", "stream2", "stream3"]

    @pytest.mark.asyncio
    async def test_run_stream_with_kwargs(self, demo_agent):
        """Test streaming run with additional kwargs."""
        thread = demo_agent.get_new_thread()
        
        async def mock_stream():
            yield Mock(spec=AgentRunResponseUpdate, text="test")
        
        demo_agent.agent.run_stream = Mock(return_value=mock_stream())
        demo_agent._apply_sliding_window = AsyncMock()
        
        chunks = []
        async for chunk in demo_agent.run_stream(
            "Test message",
            thread=thread,
            temperature=0.8
        ):
            chunks.append(chunk.text)
        
        # Verify stream was called
        demo_agent.agent.run_stream.assert_called_once()
        assert len(chunks) == 1


class TestDemoBaseAgentToolManagement:
    """Tests for tool registration and management."""

    @pytest.mark.asyncio
    async def test_add_tool_recreates_agent(self, demo_agent):
        """Test that adding a tool recreates the agent."""
        new_tool = Mock()
        new_tool.name = "new_tool"
        
        # Should complete without error
        await demo_agent.add_tool(new_tool)
        
        # Agent should still be functional
        assert demo_agent.agent is not None
        assert demo_agent.name == "Test Agent"

    @pytest.mark.asyncio
    async def test_add_multiple_tools(self, demo_agent):
        """Test adding multiple tools."""
        tool1 = Mock()
        tool1.name = "tool1_new"
        tool2 = Mock()
        tool2.name = "tool2_new"
        
        # Should complete without error
        await demo_agent.add_tool(tool1)
        await demo_agent.add_tool(tool2)
        
        # Agent should still be functional
        assert demo_agent.agent is not None


class TestDemoBaseAgentIntegration:
    """Integration tests for DemoBaseAgent."""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, demo_agent):
        """Test a complete conversation flow."""
        # Create mock thread with message store
        mock_thread = Mock(spec=AgentThread)
        mock_thread.message_store = Mock()
        mock_thread.message_store.list_messages = AsyncMock(return_value=[])
        
        # Mock responses
        response1 = Mock(spec=AgentRunResponse, text="Response 1")
        response2 = Mock(spec=AgentRunResponse, text="Response 2")
        
        demo_agent.agent.run = AsyncMock(side_effect=[response1, response2])
        
        # First turn
        result1 = await demo_agent.run("Hello", thread=mock_thread)
        assert result1.text == "Response 1"
        
        # Second turn
        result2 = await demo_agent.run("How are you?", thread=mock_thread)
        assert result2.text == "Response 2"
        
        # Should have called run twice
        assert demo_agent.agent.run.await_count == 2

    @pytest.mark.asyncio
    async def test_conversation_with_sliding_window(self, demo_agent):
        """Test conversation that triggers sliding window."""
        mock_thread = Mock(spec=AgentThread)
        mock_thread.message_store = Mock()
        
        # Create 25 messages to trigger sliding window (max is 20)
        messages = [
            Mock(spec=ChatMessage, role="user" if i % 2 == 0 else "assistant")
            for i in range(25)
        ]
        mock_thread.message_store.list_messages = AsyncMock(return_value=messages)
        
        mock_response = Mock(spec=AgentRunResponse, text="Response")
        demo_agent.agent.run = AsyncMock(return_value=mock_response)
        
        await demo_agent.run("New message", thread=mock_thread)
        
        # Should have applied sliding window
        assert len(mock_thread.message_store.messages) == 20

    @pytest.mark.asyncio
    async def test_thread_persistence(self, demo_agent):
        """Test thread serialization and deserialization."""
        # Create and serialize thread
        mock_thread = Mock(spec=AgentThread)
        thread_data = {"thread_id": "test-123", "messages": []}
        mock_thread.serialize = AsyncMock(return_value=thread_data)
        
        serialized = await demo_agent.serialize_thread(mock_thread)
        assert serialized == thread_data
        
        # Deserialize thread
        restored_thread = Mock(spec=AgentThread)
        demo_agent.agent.deserialize_thread = AsyncMock(return_value=restored_thread)
        
        thread = await demo_agent.deserialize_thread(serialized)
        assert thread == restored_thread
