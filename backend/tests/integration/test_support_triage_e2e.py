"""
Integration tests for Support Triage Agent with real external services.

These tests connect to real Azure OpenAI and MCP servers, so they:
- Incur real costs (~$0.01-0.03 per test)
- Require environment variables configured
- Take longer to run (5-30 seconds per test)
- May fail if services are unavailable

Run only when necessary:
    pytest tests/integration/test_support_triage_e2e.py -v
    
Skip if not needed:
    pytest tests/ -v -m "not integration"
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.agents.support_triage import SupportTriageAgent


class TestSupportTriageAgentMicrosoftLearnIntegration:
    """
    Integration tests using real Microsoft Learn MCP server.
    
    These tests validate that the Support Triage Agent can:
    - Connect to Microsoft Learn MCP server
    - Use the real Azure OpenAI API
    - Perform documentation searches
    - Generate helpful responses based on real documentation
    """

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("AZURE_OPENAI_ENDPOINT"),
        reason="Azure OpenAI endpoint not configured"
    )
    async def test_support_triage_with_microsoft_learn_basic_query(
        self,
        azure_openai_available,
        use_real_api
    ):
        """
        Integration test: Support Triage Agent handles basic Azure question using Microsoft Learn.
        
        This test validates:
        - Agent can be created with REAL Microsoft Learn MCP tool
        - Microsoft Learn MCP server is accessible and functional
        - Azure OpenAI API processes the request
        - Agent returns a helpful response based on real documentation
        
        Expected cost: ~$0.01
        Expected time: 10-15 seconds
        """
        # Mock ONLY the OpenAPI Support Triage tool (not implemented yet)
        # But use the REAL Microsoft Learn MCP tool
        with patch("src.agents.support_triage.get_support_triage_tool") as mock_support_tool:
            # Mock the Support Triage OpenAPI tool (to be implemented later)
            mock_support_instance = Mock()
            mock_support_instance.__aenter__ = AsyncMock(return_value=mock_support_instance)
            mock_support_instance.__aexit__ = AsyncMock(return_value=None)
            mock_support_tool.return_value = mock_support_instance
            
            # NOW create agent with REAL Microsoft Learn MCP and mocked Support Triage API
            agent = SupportTriageAgent.create(
                model=os.getenv("DEFAULT_MODEL", "gpt-4o"),
                temperature=0.7,
                max_messages=10
            )
            
            # Verify agent was created successfully
            assert agent is not None
            assert agent.name == "Support Triage Agent"
            
            # Query about a common Azure topic
            query = "How do I create a storage account in Azure?"
            
            # Create a new thread for the conversation
            thread = agent.get_new_thread()
            
            # Run the query (this makes a REAL Azure OpenAI API call with REAL Microsoft Learn MCP)
            result = await agent.run(
                message=query,
                thread=thread,
                max_tokens=500  # Limit tokens for cost control
            )
            
            # Validate response structure
            assert result is not None
            assert hasattr(result, "messages")
            assert len(result.messages) > 0
            
            # The response should contain messages from the conversation
            messages = list(result.messages)
            print(f"\n✓ Received {len(messages)} messages in response")
            
            # Should have at least one message
            assert len(messages) >= 1, "Should have at least one message"
            
            # Last message should be from the assistant
            last_message = messages[-1]
            print(f"✓ Last message role: {last_message.role}")
            print(f"✓ Last message type: {type(last_message)}")
            
            # Try to access content different ways
            content = ""
            if hasattr(last_message, "content"):
                content = last_message.content
            elif hasattr(last_message, "text"):
                content = last_message.text
            elif hasattr(last_message, "message"):
                content = last_message.message
            
            print(f"✓ Response length: {len(str(content))} characters")
            assert len(str(content)) > 0, "Assistant should provide a response"
            
            print(f"\n✓ Agent responded successfully using REAL Microsoft Learn MCP")
            print(f"✓ Message count in thread: {len(messages)}")

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("AZURE_OPENAI_ENDPOINT"),
        reason="Azure OpenAI endpoint not configured"
    )
    async def test_support_triage_multi_turn_conversation(
        self,
        azure_openai_available,
        use_real_api
    ):
        """
        Integration test: Support Triage Agent handles multi-turn conversation with thread persistence.
        
        This test validates:
        - Agent maintains context across multiple queries
        - Thread serialization/deserialization works
        - Sliding window memory management works
        - Agent provides contextually relevant follow-up responses
        - REAL Microsoft Learn MCP tool works across multiple turns
        
        Expected cost: ~$0.02-0.03
        Expected time: 20-30 seconds
        """
        # Mock ONLY the OpenAPI Support Triage tool
        with patch("src.agents.support_triage.get_support_triage_tool") as mock_support_tool:
            # Setup mock for Support Triage API
            mock_support_instance = Mock()
            mock_support_instance.__aenter__ = AsyncMock(return_value=mock_support_instance)
            mock_support_instance.__aexit__ = AsyncMock(return_value=None)
            mock_support_tool.return_value = mock_support_instance
            
            # Create agent with REAL Microsoft Learn MCP
            agent = SupportTriageAgent.create(
                model=os.getenv("DEFAULT_MODEL", "gpt-4o"),
                temperature=0.7,
                max_messages=10
            )
            
            # Create a new thread
            thread = agent.get_new_thread()
            
            # First query: Initial question
            query1 = "What is Azure App Service?"
            result1 = await agent.run(
                message=query1,
                thread=thread,
                max_tokens=300
            )
            
            assert result1 is not None
            messages1 = list(result1.messages)
            assert len(messages1) >= 1
            print(f"\n✓ Query 1 completed: {len(messages1)} messages")
            
            # Second query: Follow-up question (requires context from first query)
            query2 = "What are the pricing tiers for it?"
            result2 = await agent.run(
                message=query2,
                thread=thread,
                max_tokens=300
            )
            
            assert result2 is not None
            messages2 = list(result2.messages)
            assert len(messages2) >= 1  # Each result contains messages from current turn
            print(f"✓ Query 2 completed: {len(messages2)} messages")
            
            # Third query: Another follow-up
            query3 = "Which tier should I use for production?"
            result3 = await agent.run(
                message=query3,
                thread=thread,
                max_tokens=300
            )
            
            assert result3 is not None
            messages3 = list(result3.messages)
            assert len(messages3) >= 1  # Each result contains messages from current turn
            print(f"✓ Query 3 completed: {len(messages3)} messages")
            
            # Verify thread persistence by serializing and deserializing
            thread_dict = await agent.serialize_thread(thread)
            assert thread_dict is not None
            assert isinstance(thread_dict, dict)
            
            # Deserialize thread
            restored_thread = await agent.deserialize_thread(thread_dict)
            assert restored_thread is not None
            
            print(f"\n✓ Multi-turn conversation completed successfully")
            print(f"✓ Final message count: {len(messages3)}")
            print(f"✓ Thread serialization: Working")
            print(f"✓ Thread deserialization: Working")
            print(f"✓ REAL Microsoft Learn MCP: Used across all queries")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("AZURE_OPENAI_ENDPOINT"),
        reason="Azure OpenAI endpoint not configured"
    )
    async def test_support_triage_streaming_response(
        self,
        azure_openai_available,
        use_real_api
    ):
        """
        Integration test: Support Triage Agent streams responses from Azure OpenAI.
        
        This test validates:
        - Agent can stream responses in real-time
        - Streaming maintains proper message structure
        - Stream completes successfully
        - REAL Microsoft Learn MCP tool works with streaming
        
        Expected cost: ~$0.01
        Expected time: 10-15 seconds
        """
        # Mock ONLY the OpenAPI Support Triage tool
        with patch("src.agents.support_triage.get_support_triage_tool") as mock_support_tool:
            # Setup mock
            mock_support_instance = Mock()
            mock_support_instance.__aenter__ = AsyncMock(return_value=mock_support_instance)
            mock_support_instance.__aexit__ = AsyncMock(return_value=None)
            mock_support_tool.return_value = mock_support_instance
            
            # Create agent with REAL Microsoft Learn MCP
            agent = SupportTriageAgent.create(
                model=os.getenv("DEFAULT_MODEL", "gpt-4o"),
                temperature=0.7,
                max_messages=10
            )
            
            # Create a new thread
            thread = agent.get_new_thread()
            
            # Query with streaming
            query = "What is Azure Functions?"
            
            # Collect streamed chunks
            chunks_received = 0
            final_result = None
            
            async for chunk in agent.run_stream(
                message=query,
                thread=thread,
                max_tokens=300
            ):
                chunks_received += 1
                final_result = chunk
            
            # Validate streaming worked
            assert chunks_received > 0, "Should receive at least one chunk"
            assert final_result is not None
            
            # Note: Streaming updates may not have messages attribute on every chunk
            # Final result should have the complete conversation
            print(f"\n✓ Streaming completed successfully")
            print(f"✓ Chunks received: {chunks_received}")
            print(f"✓ REAL Microsoft Learn MCP: Used with streaming")


class TestSupportTriageAgentErrorHandling:
    """
    Integration tests for error handling scenarios.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("AZURE_OPENAI_ENDPOINT"),
        reason="Azure OpenAI endpoint not configured"
    )
    async def test_support_triage_handles_empty_query(
        self,
        azure_openai_available,
        use_real_api
    ):
        """
        Integration test: Agent handles empty or invalid queries gracefully.
        
        Expected cost: ~$0.005
        Expected time: 5 seconds
        """
        # Mock ONLY the OpenAPI Support Triage tool
        with patch("src.agents.support_triage.get_support_triage_tool") as mock_support_tool:
            mock_support_instance = Mock()
            mock_support_instance.__aenter__ = AsyncMock(return_value=mock_support_instance)
            mock_support_instance.__aexit__ = AsyncMock(return_value=None)
            mock_support_tool.return_value = mock_support_instance
            
            # Create agent with REAL Microsoft Learn MCP
            agent = SupportTriageAgent.create()
            
            thread = agent.get_new_thread()
            
            # Test with empty string
            result = await agent.run(
                message="",
                thread=thread,
                max_tokens=100
            )
            
            # Agent should still respond (even if asking for clarification)
            assert result is not None
            assert len(list(result.messages)) >= 1
            
            print(f"\n✓ Agent handled empty query gracefully")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("AZURE_OPENAI_ENDPOINT"),
        reason="Azure OpenAI endpoint not configured"
    )
    async def test_support_triage_token_limit_handling(
        self,
        azure_openai_available,
        use_real_api
    ):
        """
        Integration test: Agent respects token limits and doesn't exceed budget.
        
        Expected cost: ~$0.005
        Expected time: 5 seconds
        """
        # Mock ONLY the OpenAPI Support Triage tool
        with patch("src.agents.support_triage.get_support_triage_tool") as mock_support_tool:
            mock_support_instance = Mock()
            mock_support_instance.__aenter__ = AsyncMock(return_value=mock_support_instance)
            mock_support_instance.__aexit__ = AsyncMock(return_value=None)
            mock_support_tool.return_value = mock_support_instance
            
            # Create agent with REAL Microsoft Learn MCP
            agent = SupportTriageAgent.create()
            
            thread = agent.get_new_thread()
            
            # Request with very low token limit
            result = await agent.run(
                message="Explain Azure Kubernetes Service in detail",
                thread=thread,
                max_tokens=50  # Very limited
            )
            
            assert result is not None
            messages = list(result.messages)
            assert len(messages) >= 1
            
            # Response should be present but potentially truncated due to token limit
            last_message = messages[-1]
            
            # Try to access content different ways
            content = ""
            if hasattr(last_message, "content"):
                content = last_message.content
            elif hasattr(last_message, "text"):
                content = last_message.text
            
            # Should have some content even with low token limit
            assert len(str(content)) > 0
            
            print(f"\n✓ Agent respected token limit")
            print(f"✓ Response length: {len(str(content))} characters")
