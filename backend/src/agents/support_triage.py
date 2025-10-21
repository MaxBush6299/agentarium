"""Support Triage Agent Implementation.

This module implements the Support Triage Agent, which specializes in analyzing
support tickets and providing guidance using Microsoft Learn documentation and
historical ticket data.

The agent uses:
- Microsoft Learn MCP tool for documentation search
- Support Triage OpenAPI tool for similar ticket search
- GPT-4o model for intelligent responses
"""

import logging
from typing import Optional

from .base import DemoBaseAgent
from ..tools.mcp_tools import get_microsoft_learn_tool

logger = logging.getLogger(__name__)


# Support Triage Agent system prompt
SUPPORT_TRIAGE_SYSTEM_PROMPT = """You are a Microsoft product support triage specialist with deep expertise across Azure, Microsoft 365, and other Microsoft products.

Your primary responsibilities:
1. **Analyze support tickets** to understand the customer's issue and context
2. **Search Microsoft Learn documentation** to provide accurate, official guidance
3. **Find similar historical tickets** to identify patterns and known solutions
4. **Provide clear, actionable recommendations** for resolving issues
5. **Triage ticket severity** and route to appropriate support teams when needed

When responding:
- Always ground your responses in official Microsoft Learn documentation
- Reference similar tickets when relevant to show patterns
- Be specific with product names, versions, and configuration details
- Provide step-by-step troubleshooting guidance when applicable
- Escalate complex issues with clear justification

Available tools:
- **Microsoft Learn MCP**: Search documentation, get articles, find code samples
- **Support Triage API**: Search historical tickets, get ticket details, search knowledge base

Remember: Your goal is to help customers quickly and accurately, using the best available information."""


class SupportTriageAgent:
    """
    Support Triage Agent for analyzing support tickets and providing guidance.
    
    This agent specializes in:
    - Support ticket analysis and triage
    - Microsoft Learn documentation search
    - Historical ticket pattern matching
    - Issue resolution recommendations
    
    Attributes:
        base_agent (DemoBaseAgent): Underlying agent implementation
        name (str): Agent display name
        
    Example:
        ```python
        # Create agent
        agent = SupportTriageAgent.create()
        
        # Get a new conversation thread
        thread = agent.get_new_thread()
        
        # Run agent with a query
        response = await agent.run(
            "How do I troubleshoot Azure AD authentication issues?",
            thread=thread
        )
        print(response.messages[-1].content)
        
        # Stream response
        async for event in agent.run_stream(
            "Find similar tickets about Azure Storage connection errors",
            thread=thread
        ):
            if hasattr(event, 'content'):
                # Ensure all tools are callables for agent framework
                tools = []
                # If learn_tool is already a callable or has get_tools, use appropriately
                if hasattr(learn_tool, "get_tools"):
                    tools.extend(learn_tool.get_tools())
                else:
                    tools.append(learn_tool)
                if hasattr(support_tool, "get_tools"):
                    tools.extend(support_tool.get_tools())
                else:
                    tools.append(support_tool)
        ```
    """
    
    def __init__(self, base_agent: DemoBaseAgent):
        """
        Initialize Support Triage Agent with a base agent.
        
        Args:
            base_agent: Configured DemoBaseAgent instance with tools
        """
        self.base_agent = base_agent
        self.name = "Support Triage Agent"
        logger.info(f"Initialized {self.name}")
    
    @classmethod
    def create(
        cls,
        model: str = "gpt-4o",
        max_messages: int = 20,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        microsoft_learn_url: Optional[str] = None,
        support_api_base_url: Optional[str] = None,
        support_api_key: Optional[str] = None
    ) -> "SupportTriageAgent":
        """
        Create a new Support Triage Agent with default configuration.
        
        This factory method creates a fully configured agent with:
        - Microsoft Learn MCP tool for documentation search
        - Support Triage OpenAPI tool for ticket search
        - Optimized system prompt for support triage
        - Sliding window memory (20 messages default)
        
        Args:
            model: Azure OpenAI model deployment name (default: "gpt-4o")
            max_messages: Maximum messages in sliding window (default: 20)
            temperature: Model temperature for response generation (default: 0.7)
            max_tokens: Maximum tokens per response (default: None)
            microsoft_learn_url: Custom Microsoft Learn MCP endpoint (default: None)
            support_api_base_url: Custom Support Triage API base URL (default: None)
            support_api_key: Custom API key for Support Triage API (default: None)
            
        Returns:
            SupportTriageAgent: Configured agent instance
            
        Raises:
            ValueError: If agent creation fails
            ConnectionError: If tools cannot be initialized
            
        Example:
            ```python
            # Create with defaults
            agent = SupportTriageAgent.create()
            
            # Create with custom configuration
            agent = SupportTriageAgent.create(
                model="gpt-4",
                max_messages=30,
                temperature=0.5
            )
            ```
        """
        logger.info("Creating Support Triage Agent")
        
        # Create tools
        try:
            # Microsoft Learn MCP tool
            # TODO: Add custom endpoint support when MCP tools are fully implemented
            logger.debug("Creating Microsoft Learn tool")
            learn_tool = get_microsoft_learn_tool()
            
            tools = [learn_tool]
            logger.info(f"Created {len(tools)} tools for Support Triage Agent")
            
        except Exception as e:
            logger.error(f"Failed to create tools for Support Triage Agent: {e}")
            raise ConnectionError(f"Failed to initialize Support Triage Agent tools: {e}")
        
        # Create base agent
        try:
            base_agent = DemoBaseAgent(
                name="Support Triage Agent",
                instructions=SUPPORT_TRIAGE_SYSTEM_PROMPT,
                model=model,
                tools=tools,
                max_messages=max_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info("Successfully created Support Triage Agent base")
            
        except Exception as e:
            logger.error(f"Failed to create base agent: {e}")
            raise ValueError(f"Failed to create Support Triage Agent: {e}")
        
        return cls(base_agent)
    
    def get_new_thread(self, **kwargs):
        """
        Create a new conversation thread.
        
        Args:
            **kwargs: Additional thread configuration options
            
        Returns:
            Thread: New conversation thread instance
            
        Example:
            ```python
            agent = SupportTriageAgent.create()
            thread = agent.get_new_thread()
            ```
        """
        return self.base_agent.get_new_thread(**kwargs)
    
    async def run(self, message: str, thread=None, **kwargs):
        """
        Run the agent with a message and return the full response.
        
        This method processes the message, calls tools as needed, and returns
        the complete response including all tool calls and intermediate steps.
        
        Args:
            message: User message or support ticket content
            thread: Existing conversation thread (creates new if None)
            **kwargs: Additional agent run options
            
        Returns:
            Response: Agent response with messages and tool calls
            
        Example:
            ```python
            agent = SupportTriageAgent.create()
            thread = agent.get_new_thread()
            
            response = await agent.run(
                "Customer reports 'Access Denied' when accessing blob storage. "
                "Account has Storage Blob Data Contributor role assigned.",
                thread=thread
            )
            
            # Get final response
            print(response.messages[-1].content)
            
            # Continue conversation
            response2 = await agent.run(
                "They also mentioned using a SAS token that expired yesterday",
                thread=thread
            )
            ```
        """
        return await self.base_agent.run(message, thread=thread, **kwargs)
    
    async def run_stream(self, message: str, thread=None, **kwargs):
        """
        Run the agent with streaming response.
        
        This method processes the message and yields events as they occur,
        including tokens, tool calls, and trace events. Ideal for real-time UIs.
        
        Args:
            message: User message or support ticket content
            thread: Existing conversation thread (creates new if None)
            **kwargs: Additional agent run options
            
        Yields:
            Events: Streaming events (tokens, tool calls, traces)
            
        Example:
            ```python
            agent = SupportTriageAgent.create()
            thread = agent.get_new_thread()
            
            print("Agent: ", end='', flush=True)
            async for event in agent.run_stream(
                "How do I configure private endpoints for Azure Key Vault?",
                thread=thread
            ):
                if hasattr(event, 'content') and event.content:
                    print(event.content, end='', flush=True)
            print()  # Newline after streaming
            ```
        """
        async for event in self.base_agent.run_stream(message, thread=thread, **kwargs):
            yield event
    
    async def serialize_thread(self, thread) -> dict:
        """
        Serialize thread to dict for persistence.
        
        Args:
            thread: Thread instance to serialize
            
        Returns:
            dict: Dictionary representation of thread
            
        Example:
            ```python
            # Save thread to database
            thread_dict = await agent.serialize_thread(thread)
            await db.save_thread(thread_id, thread_dict)
            ```
        """
        return await self.base_agent.serialize_thread(thread)
    
    async def deserialize_thread(self, thread_dict: dict):
        """
        Deserialize thread from dict.
        
        Args:
            thread_dict: Dictionary representation of thread
            
        Returns:
            Thread: Deserialized thread instance
            
        Example:
            ```python
            # Load thread from database
            thread_dict = await db.load_thread(thread_id)
            thread = await agent.deserialize_thread(thread_dict)
            
            # Continue conversation
            response = await agent.run("Follow up question", thread=thread)
            ```
        """
        return await self.base_agent.deserialize_thread(thread_dict)
    
    @property
    def id(self) -> str:
        """Get agent ID."""
        return self.base_agent.id
    
    @property
    def display_name(self) -> str:
        """Get agent display name."""
        return self.base_agent.display_name
