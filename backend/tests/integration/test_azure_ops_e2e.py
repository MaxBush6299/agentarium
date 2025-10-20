"""
Integration tests for Azure Ops Assistant Agent.

These tests verify end-to-end functionality of the Azure Ops Agent including:
- Agent creation and initialization
- Tool integration (Azure MCP and Ops Assistant API)
- Natural language query processing
- Resource discovery and monitoring
- Deployment status checks
- Log analysis

Note: These tests mock external services (Azure MCP server, Ops Assistant API)
to ensure reliable, fast test execution without external dependencies.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.azure_ops import AzureOpsAgent
from agent_framework import AgentRunResponse


@pytest.fixture
def mock_azure_mcp_tool():
    """Mock Azure MCP tool for testing."""
    mock_tool = MagicMock()
    mock_tool.name = "azure_mcp"
    mock_tool.description = "Azure MCP tool for resource management"
    return mock_tool


@pytest.fixture
def mock_ops_api_tool():
    """Mock Ops Assistant API tool for testing."""
    mock_tool = MagicMock()
    mock_tool.name = "ops_assistant_api"
    mock_tool.description = "Ops Assistant API for deployment operations"
    return mock_tool


@pytest.fixture
def mock_base_agent(mock_azure_mcp_tool, mock_ops_api_tool):
    """Mock DemoBaseAgent for testing."""
    mock_agent = MagicMock()
    mock_agent.name = "Azure Ops Assistant"
    mock_agent.agent = MagicMock()
    mock_agent.agent.id = "test-agent-123"
    
    # Mock run method to return AgentRunResponse
    async def mock_run(message, thread=None, **kwargs):
        # Create mock response based on message content
        response = MagicMock(spec=AgentRunResponse)
        response.text = f"Mock response for: {message}"
        response.messages = [
            MagicMock(role="user", content=message),
            MagicMock(role="assistant", content=f"Mock response for: {message}")
        ]
        response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        return response
    
    # Mock run_stream method - return async generator directly
    async def mock_run_stream(message, thread=None, **kwargs):
        chunks = ["Mock ", "streaming ", "response"]
        for chunk in chunks:
            update = MagicMock()
            update.text = chunk
            yield update
    
    mock_agent.run = AsyncMock(side_effect=mock_run)
    mock_agent.run_stream = mock_run_stream  # Don't wrap in AsyncMock
    mock_agent.get_new_thread = MagicMock(return_value=MagicMock())
    
    return mock_agent


@pytest.mark.asyncio
class TestAzureOpsAgentCreation:
    """Test Azure Ops Agent creation and initialization."""
    
    async def test_create_agent_with_defaults(self, mock_azure_mcp_tool, mock_ops_api_tool):
        """Test creating agent with default configuration."""
        with patch('src.agents.azure_ops.get_azure_mcp_tool', return_value=mock_azure_mcp_tool), \
             patch('src.agents.azure_ops.get_ops_assistant_tool', return_value=mock_ops_api_tool), \
             patch('src.agents.azure_ops.DemoBaseAgent') as mock_base_agent_class:
            
            # Setup mock base agent
            mock_base = MagicMock()
            mock_base_agent_class.return_value = mock_base
            
            # Create agent
            agent = AzureOpsAgent.create()
            
            # Verify agent was created
            assert agent is not None
            assert agent.name == "Azure Ops Assistant"
            
            # Verify base agent was created with correct parameters
            mock_base_agent_class.assert_called_once()
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['name'] == "Azure Ops Assistant"
            assert call_kwargs['model'] == "gpt-4o"
            assert call_kwargs['temperature'] == 0.7
            assert len(call_kwargs['tools']) == 2  # Azure MCP + Ops API
    
    async def test_create_agent_with_custom_config(self, mock_azure_mcp_tool, mock_ops_api_tool):
        """Test creating agent with custom configuration."""
        with patch('src.agents.azure_ops.get_azure_mcp_tool', return_value=mock_azure_mcp_tool), \
             patch('src.agents.azure_ops.get_ops_assistant_tool', return_value=mock_ops_api_tool), \
             patch('src.agents.azure_ops.DemoBaseAgent') as mock_base_agent_class:
            
            mock_base = MagicMock()
            mock_base_agent_class.return_value = mock_base
            
            # Create agent with custom config
            agent = AzureOpsAgent.create(
                model="gpt-4",
                temperature=0.5,
                max_tokens=1000,
                max_messages=15
            )
            
            # Verify custom parameters were used
            call_kwargs = mock_base_agent_class.call_args[1]
            assert call_kwargs['model'] == "gpt-4"
            assert call_kwargs['temperature'] == 0.5
            assert call_kwargs['max_tokens'] == 1000
            assert call_kwargs['max_messages'] == 15
    
    async def test_create_agent_azure_mcp_only(self, mock_azure_mcp_tool):
        """Test creating agent with only Azure MCP tool."""
        with patch('src.agents.azure_ops.get_azure_mcp_tool', return_value=mock_azure_mcp_tool), \
             patch('src.agents.azure_ops.get_ops_assistant_tool', side_effect=Exception("API unavailable")), \
             patch('src.agents.azure_ops.DemoBaseAgent') as mock_base_agent_class:
            
            mock_base = MagicMock()
            mock_base_agent_class.return_value = mock_base
            
            # Create agent (should succeed with just Azure MCP)
            agent = AzureOpsAgent.create()
            
            # Verify agent was created with 1 tool
            call_kwargs = mock_base_agent_class.call_args[1]
            assert len(call_kwargs['tools']) == 1
    
    async def test_create_agent_no_tools_fails(self):
        """Test that agent creation fails if no tools are available."""
        with patch('src.agents.azure_ops.get_azure_mcp_tool', side_effect=Exception("MCP unavailable")), \
             patch('src.agents.azure_ops.get_ops_assistant_tool', side_effect=Exception("API unavailable")):
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="Failed to initialize any tools"):
                AzureOpsAgent.create()


@pytest.mark.asyncio
class TestAzureOpsAgentOperations:
    """Test Azure Ops Agent query processing and operations."""
    
    async def test_resource_discovery_query(self, mock_base_agent):
        """Test resource discovery query."""
        agent = AzureOpsAgent(mock_base_agent)
        
        # Query for resources
        response = await agent.run(
            "List all Container Apps in the production resource group"
        )
        
        # Verify response
        assert response is not None
        assert "Mock response" in response.text
        mock_base_agent.run.assert_called_once()
    
    async def test_deployment_status_query(self, mock_base_agent):
        """Test deployment status query."""
        agent = AzureOpsAgent(mock_base_agent)
        
        # Query deployment status
        response = await agent.run(
            "What is the current deployment status for production?"
        )
        
        # Verify response
        assert response is not None
        assert "Mock response" in response.text
    
    async def test_log_analysis_query(self, mock_base_agent):
        """Test log analysis query."""
        agent = AzureOpsAgent(mock_base_agent)
        
        # Query for logs
        response = await agent.run(
            "Show me error logs from the backend Container App in the last hour"
        )
        
        # Verify response
        assert response is not None
        assert "Mock response" in response.text
    
    async def test_streaming_response(self, mock_base_agent):
        """Test streaming responses."""
        agent = AzureOpsAgent(mock_base_agent)
        
        # Call run_stream and collect chunks
        chunks = []
        stream = agent.run_stream("List all storage accounts")
        async for update in stream:
            chunks.append(update.text)
        
        # Verify chunks were received
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert "Mock streaming response" == full_response


@pytest.mark.asyncio
class TestAzureOpsConvenienceMethods:
    """Test convenience methods for common Azure operations."""
    
    async def test_list_resources_all(self, mock_base_agent):
        """Test listing all resources."""
        agent = AzureOpsAgent(mock_base_agent)
        
        response = await agent.list_resources()
        
        # Verify correct query was made
        assert response is not None
        call_args = mock_base_agent.run.call_args
        assert "List Azure resources" in call_args[0][0]
    
    async def test_list_resources_by_group(self, mock_base_agent):
        """Test listing resources by resource group."""
        agent = AzureOpsAgent(mock_base_agent)
        
        response = await agent.list_resources(resource_group="rg-production")
        
        # Verify query includes resource group filter
        call_args = mock_base_agent.run.call_args
        query = call_args[0][0]
        assert "rg-production" in query
        assert "resource group" in query
    
    async def test_list_resources_by_type(self, mock_base_agent):
        """Test listing resources by type."""
        agent = AzureOpsAgent(mock_base_agent)
        
        response = await agent.list_resources(resource_type="Microsoft.App/containerApps")
        
        # Verify query includes resource type filter
        call_args = mock_base_agent.run.call_args
        query = call_args[0][0]
        assert "Microsoft.App/containerApps" in query
        assert "type" in query
    
    async def test_list_resources_both_filters(self, mock_base_agent):
        """Test listing resources with both group and type filters."""
        agent = AzureOpsAgent(mock_base_agent)
        
        response = await agent.list_resources(
            resource_group="rg-production",
            resource_type="Microsoft.App/containerApps"
        )
        
        # Verify query includes both filters
        call_args = mock_base_agent.run.call_args
        query = call_args[0][0]
        assert "rg-production" in query
        assert "Microsoft.App/containerApps" in query
    
    async def test_get_deployment_status(self, mock_base_agent):
        """Test getting deployment status."""
        agent = AzureOpsAgent(mock_base_agent)
        
        response = await agent.get_deployment_status(environment="staging")
        
        # Verify correct query was made
        call_args = mock_base_agent.run.call_args
        query = call_args[0][0]
        assert "deployment status" in query
        assert "staging" in query
    
    async def test_analyze_logs(self, mock_base_agent):
        """Test log analysis."""
        agent = AzureOpsAgent(mock_base_agent)
        
        response = await agent.analyze_logs(
            resource_name="backend-api",
            time_range="last 24 hours"
        )
        
        # Verify correct query was made
        call_args = mock_base_agent.run.call_args
        query = call_args[0][0]
        assert "backend-api" in query
        assert "last 24 hours" in query
        assert "logs" in query.lower()


@pytest.mark.asyncio
class TestAzureOpsAgentThread:
    """Test conversation threading and context management."""
    
    async def test_single_turn_conversation(self, mock_base_agent):
        """Test single-turn conversation."""
        agent = AzureOpsAgent(mock_base_agent)
        
        response = await agent.run("List all resources")
        
        assert response is not None
        mock_base_agent.run.assert_called_once()
    
    async def test_multi_turn_conversation(self, mock_base_agent):
        """Test multi-turn conversation with thread."""
        agent = AzureOpsAgent(mock_base_agent)
        thread = agent.get_new_thread()
        
        # Turn 1
        response1 = await agent.run(
            "List all Container Apps in production",
            thread=thread
        )
        assert response1 is not None
        
        # Turn 2 (with context)
        response2 = await agent.run(
            "Show me logs from the first one",
            thread=thread
        )
        assert response2 is not None
        
        # Verify both calls were made with the same thread
        assert mock_base_agent.run.call_count == 2
    
    async def test_get_new_thread(self, mock_base_agent):
        """Test creating new threads."""
        agent = AzureOpsAgent(mock_base_agent)
        
        thread1 = agent.get_new_thread()
        thread2 = agent.get_new_thread()
        
        # Verify threads were created
        assert thread1 is not None
        assert thread2 is not None
        assert mock_base_agent.get_new_thread.call_count == 2


@pytest.mark.asyncio
class TestAzureOpsAgentRealWorldScenarios:
    """Test realistic end-to-end scenarios."""
    
    async def test_troubleshooting_scenario(self, mock_base_agent):
        """Test a complete troubleshooting workflow."""
        agent = AzureOpsAgent(mock_base_agent)
        thread = agent.get_new_thread()
        
        # Step 1: User reports an issue
        await agent.run(
            "The backend API is returning 500 errors",
            thread=thread
        )
        
        # Step 2: Check resource health
        await agent.run(
            "Check the health status of the backend Container App",
            thread=thread
        )
        
        # Step 3: Analyze logs
        await agent.analyze_logs(
            resource_name="backend-api",
            time_range="last 1 hour",
            thread=thread
        )
        
        # Step 4: Check recent deployments
        await agent.get_deployment_status(
            environment="production",
            thread=thread
        )
        
        # Verify all interactions happened with context
        assert mock_base_agent.run.call_count == 4
    
    async def test_monitoring_scenario(self, mock_base_agent):
        """Test a monitoring/inspection workflow."""
        agent = AzureOpsAgent(mock_base_agent)
        thread = agent.get_new_thread()
        
        # Check deployment status
        await agent.get_deployment_status(thread=thread)
        
        # List all resources
        await agent.list_resources(resource_group="rg-production", thread=thread)
        
        # Check specific resource logs
        await agent.analyze_logs("frontend-web", thread=thread)
        
        # Verify all operations were performed
        assert mock_base_agent.run.call_count == 3
    
    async def test_resource_discovery_scenario(self, mock_base_agent):
        """Test resource discovery and exploration."""
        agent = AzureOpsAgent(mock_base_agent)
        thread = agent.get_new_thread()
        
        # Broad discovery
        await agent.list_resources(thread=thread)
        
        # Filter by resource group
        await agent.list_resources(
            resource_group="rg-production",
            thread=thread
        )
        
        # Filter by type
        await agent.list_resources(
            resource_type="Microsoft.App/containerApps",
            thread=thread
        )
        
        # Specific resource details
        await agent.run(
            "Tell me more about the backend-api Container App",
            thread=thread
        )
        
        # Verify discovery workflow
        assert mock_base_agent.run.call_count == 4
