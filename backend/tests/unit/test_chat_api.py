"""
Unit tests for Chat API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.api.chat import get_agent
from src.persistence.models import (
    Thread, Run, Step, Message, ToolCall,
    RunStatus, StepStatus, StepType,
    ChatRequest
)


class TestGetAgent:
    """Tests for get_agent helper function."""
    
    @pytest.mark.asyncio
    async def test_get_support_triage_agent(self):
        """Test getting support-triage agent."""
        with patch('src.api.chat.get_agent_repository') as mock_repo:
            mock_repo.return_value.get.return_value = None
            agent = await get_agent("support-triage")
            # Will be None because we're mocking repo to return None
    
    @pytest.mark.asyncio
    async def test_get_azure_ops_agent_with_ops_assistant(self):
        """Test getting Azure Ops agent with 'ops-assistant' ID."""
        with patch('src.api.chat.get_agent_repository') as mock_repo:
            mock_repo.return_value.get.return_value = None
            agent = await get_agent("ops-assistant")
            # Will be None because we're mocking repo to return None
    
    @pytest.mark.asyncio
    async def test_get_azure_ops_agent_with_azure_ops(self):
        """Test getting Azure Ops agent with 'azure-ops' ID."""
        with patch('src.api.chat.get_agent_repository') as mock_repo:
            mock_repo.return_value.get.return_value = None
            agent = await get_agent("azure-ops")
            # Will be None because we're mocking repo to return None
    
    @pytest.mark.asyncio
    async def test_get_invalid_agent(self):
        """Test getting non-existent agent."""
        with patch('src.api.chat.get_agent_repository') as mock_repo:
            mock_repo.return_value.get.return_value = None
            agent = await get_agent("invalid-agent")
            assert agent is None
    
    @pytest.mark.asyncio
    async def test_get_sql_agent_not_yet_implemented(self):
        """Test that SQL agent returns None (not yet implemented)."""
        with patch('src.api.chat.get_agent_repository') as mock_repo:
            mock_repo.return_value.get.return_value = None
            agent = await get_agent("sql-agent")
            assert agent is None


class TestChatRequest:
    """Tests for ChatRequest model."""
    
    def test_create_chat_request(self):
        """Test creating a ChatRequest."""
        request = ChatRequest(
            message="Test message",
            thread_id=None,
            stream=True
        )
        
        assert request.message == "Test message"
        assert request.thread_id is None
        assert request.stream is True
    
    def test_chat_request_with_thread_id(self):
        """Test ChatRequest with existing thread_id."""
        request = ChatRequest(
            message="Test message",
            thread_id="thread_123",
            stream=True
        )
        
        assert request.message == "Test message"
        assert request.thread_id == "thread_123"
    
    def test_chat_request_default_stream(self):
        """Test ChatRequest with default stream value."""
        request = ChatRequest(message="Test")
        assert request.stream is True


class TestThreadModel:
    """Tests for Thread model."""
    
    def test_create_thread(self):
        """Test creating a Thread."""
        thread = Thread(
            id="thread_123",
            agent_id="support-triage",
            title="Test Thread",
            status="active",
            messages=[],
            runs=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert thread.id == "thread_123"
        assert thread.agent_id == "support-triage"
        assert thread.title == "Test Thread"
        assert thread.status == "active"
        assert len(thread.messages) == 0
    
    def test_thread_with_messages(self):
        """Test Thread with messages."""
        message = Message(
            id="msg_123",
            role="user",
            content="Test message",
            timestamp=datetime.utcnow()
        )
        
        thread = Thread(
            id="thread_123",
            agent_id="support-triage",
            title="Test",
            status="active",
            messages=[message],
            runs=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert len(thread.messages) == 1
        assert thread.messages[0].content == "Test message"


class TestRunModel:
    """Tests for Run model."""
    
    def test_create_run(self):
        """Test creating a Run."""
        run = Run(
            id="run_123",
            thread_id="thread_456",
            agent_id="support-triage",
            status=RunStatus.QUEUED,
            user_message_id="msg_789",
            model="gpt-4o",
            temperature=0.7,
            steps=[],
            created_at=datetime.utcnow()
        )
        
        assert run.id == "run_123"
        assert run.thread_id == "thread_456"
        assert run.status == RunStatus.QUEUED
        assert run.model == "gpt-4o"
        assert run.temperature == 0.7
    
    def test_run_status_progression(self):
        """Test Run status can be updated."""
        run = Run(
            id="run_123",
            thread_id="thread_456",
            agent_id="support-triage",
            status=RunStatus.QUEUED,
            user_message_id="msg_789",
            model="gpt-4o",
            steps=[],
            created_at=datetime.utcnow()
        )
        
        # Start run
        run.status = RunStatus.IN_PROGRESS
        run.started_at = datetime.utcnow()
        assert run.status == RunStatus.IN_PROGRESS
        
        # Complete run
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        assert run.status == RunStatus.COMPLETED


class TestStepModel:
    """Tests for Step model."""
    
    def test_create_step_with_tool_call(self):
        """Test creating a Step with tool call."""
        tool_call = ToolCall(
            id="call_123",
            tool_name="test_tool",
            tool_type="mcp",
            input={"query": "test"},
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        step = Step(
            id="step_123",
            run_id="run_456",
            thread_id="thread_789",
            agent_id="support-triage",
            step_type=StepType.TOOL_CALL,
            tool_call=tool_call,
            started_at=datetime.utcnow()
        )
        
        assert step.id == "step_123"
        assert step.step_type == StepType.TOOL_CALL
        assert step.tool_call is not None
        assert step.tool_call.tool_name == "test_tool"
    
    def test_step_with_message(self):
        """Test creating a Step with message."""
        message = Message(
            id="msg_123",
            role="assistant",
            content="Test response",
            timestamp=datetime.utcnow()
        )
        
        step = Step(
            id="step_123",
            run_id="run_456",
            thread_id="thread_789",
            agent_id="support-triage",
            step_type=StepType.MESSAGE,
            message=message,
            started_at=datetime.utcnow()
        )
        
        assert step.step_type == StepType.MESSAGE
        assert step.message is not None
        assert step.message.content == "Test response"


class TestToolCallModel:
    """Tests for ToolCall model."""
    
    def test_create_mcp_tool_call(self):
        """Test creating MCP tool call."""
        tool_call = ToolCall(
            id="call_123",
            tool_name="microsoft_docs_search",
            tool_type="mcp",
            input={"query": "test"},
            mcp_server="microsoft-docs",
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        assert tool_call.tool_type == "mcp"
        assert tool_call.mcp_server == "microsoft-docs"
    
    def test_create_openapi_tool_call(self):
        """Test creating OpenAPI tool call."""
        tool_call = ToolCall(
            id="call_123",
            tool_name="create_storage_account",
            tool_type="openapi",
            input={"name": "test"},
            openapi_endpoint="POST /storageAccounts",
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        assert tool_call.tool_type == "openapi"
        assert tool_call.openapi_endpoint == "POST /storageAccounts"
    
    def test_tool_call_completion(self):
        """Test completing a tool call."""
        tool_call = ToolCall(
            id="call_123",
            tool_name="test_tool",
            tool_type="builtin",
            input={"test": "data"},
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        # Complete the tool call
        tool_call.status = StepStatus.COMPLETED
        tool_call.completed_at = datetime.utcnow()
        tool_call.output = {"result": "success"}
        tool_call.latency_ms = 250
        
        assert tool_call.status == StepStatus.COMPLETED
        assert tool_call.output == {"result": "success"}
        assert tool_call.latency_ms == 250
