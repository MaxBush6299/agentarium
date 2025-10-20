"""
Base agent implementation using Microsoft Agent Framework.

This module provides the base agent class that wraps ChatAgent from agent_framework
and adds our application-specific features like sliding window memory, token counting,
and tool management.
"""
from typing import Any, Optional, Sequence
from collections.abc import AsyncIterable
import os
import logging

from agent_framework import (
    ChatAgent,
    AgentThread,
    ChatMessage,
    AgentRunResponse,
    AgentRunResponseUpdate,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


class DemoBaseAgent:
    """
    Base wrapper around ChatAgent from Microsoft Agent Framework.
    
    Provides application-specific features:
    - Sliding window memory management (max 20 messages)
    - Token counting and budget enforcement  
    - Standardized tool registration
    - Azure OpenAI integration with Managed Identity
    - Thread/conversation management
    
    Usage:
        ```python
        # Create an agent with tools
        agent = DemoBaseAgent(
            name="Support Triage Agent",
            instructions="You are a helpful support assistant...",
            tools=[microsoft_learn_tool, support_api_tool],
            model="gpt-4o"
        )
        
        # Use with a thread for conversation context
        thread = agent.get_new_thread()
        response = await agent.run("Help me troubleshoot Azure AD auth", thread=thread)
        print(response.text)
        
        # Stream responses
        async for chunk in agent.run_stream("What about RBAC?", thread=thread):
            print(chunk.text, end="", flush=True)
        ```
    """
    
    def __init__(
        self,
        name: str,
        instructions: str,
        tools: Optional[Sequence[Any]] = None,
        model: str = "gpt-4o",
        max_messages: int = 20,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ):
        """
        Initialize the agent.
        
        Args:
            name: Agent name
            instructions: System instructions/prompt for the agent
            tools: List of tools to register (MCP tools, OpenAPI tools, functions)
            model: Azure OpenAI deployment name (default: gpt-4o)
            max_messages: Maximum messages in sliding window (default: 20)
            max_tokens: Maximum tokens per request (optional)
            temperature: Temperature for generation (default: 0.7)
        """
        self.name = name
        self.instructions = instructions
        self.model = model
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize Azure OpenAI client with Managed Identity
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
        
        logger.info(f"Initializing agent '{name}' with model '{model}'")
        
        # Create the ChatAgent using Azure OpenAI Responses client
        chat_client = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=model,
            credential=DefaultAzureCredential(),
        )
        
        # Create the ChatAgent with tools
        self.agent = chat_client.create_agent(
            name=name,
            instructions=instructions,
            tools=tools if tools else [],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        logger.info(f"Agent '{name}' initialized successfully (ID: {self.agent.id})")
    
    async def run(
        self,
        message: str | ChatMessage | list[str] | list[ChatMessage],
        thread: Optional[AgentThread] = None,
        **kwargs: Any
    ) -> AgentRunResponse:
        """
        Execute the agent and return a complete response.
        
        Args:
            message: User message(s) to process
            thread: Optional conversation thread (for maintaining context)
            **kwargs: Additional arguments passed to agent.run()
            
        Returns:
            AgentRunResponse containing the agent's reply
        """
        # If no thread provided, create a new one
        if thread is None:
            thread = self.get_new_thread()
        
        # Apply sliding window if thread has too many messages
        await self._apply_sliding_window(thread)
        
        logger.debug(f"Running agent '{self.name}' with message")
        
        # Run the agent
        response = await self.agent.run(
            messages=message,
            thread=thread,
            **kwargs
        )
        
        logger.debug(f"Agent '{self.name}' completed response")
        
        return response
    
    async def run_stream(
        self,
        message: str | ChatMessage | list[str] | list[ChatMessage],
        thread: Optional[AgentThread] = None,
        **kwargs: Any
    ) -> AsyncIterable[AgentRunResponseUpdate]:
        """
        Execute the agent and stream response updates.
        
        Args:
            message: User message(s) to process
            thread: Optional conversation thread (for maintaining context)
            **kwargs: Additional arguments passed to agent.run_stream()
            
        Yields:
            AgentRunResponseUpdate objects containing chunks of the response
        """
        # If no thread provided, create a new one
        if thread is None:
            thread = self.get_new_thread()
        
        # Apply sliding window if thread has too many messages
        await self._apply_sliding_window(thread)
        
        logger.debug(f"Streaming response from agent '{self.name}'")
        
        # Stream the agent response
        async for update in self.agent.run_stream(
            messages=message,
            thread=thread,
            **kwargs
        ):
            yield update
    
    def get_new_thread(self, **kwargs: Any) -> AgentThread:
        """
        Create a new conversation thread.
        
        Args:
            **kwargs: Additional arguments for thread creation
            
        Returns:
            A new AgentThread instance
        """
        return self.agent.get_new_thread(**kwargs)
    
    async def _apply_sliding_window(self, thread: AgentThread) -> None:
        """
        Apply sliding window memory management to the thread.
        
        Keeps only the last N messages to prevent context window overflow.
        
        Args:
            thread: The thread to apply sliding window to
        """
        if thread.message_store is None:
            return
        
        messages = await thread.message_store.list_messages()
        
        # If we exceed max_messages, keep only the most recent ones
        if len(messages) > self.max_messages:
            logger.debug(f"Applying sliding window: {len(messages)} -> {self.max_messages} messages")
            
            # Keep the last max_messages messages
            recent_messages = messages[-self.max_messages:]
            
            # Clear and re-add only recent messages
            thread.message_store.messages = list(recent_messages)
    
    async def add_tool(self, tool: Any) -> None:
        """
        Add a tool to the agent dynamically.
        
        Note: This creates a new agent instance with the updated tool list.
        For best performance, register all tools during initialization.
        
        Args:
            tool: Tool to add (function, MCP tool, or OpenAPI tool)
        """
        logger.warning(f"Dynamically adding tool to agent '{self.name}' - this recreates the agent")
        
        # Get current tools from agent
        current_tools = getattr(self.agent, '_tools', []) or []
        
        # Create new tool list
        new_tools = list(current_tools) + [tool]
        
        # Recreate the agent with the new tools
        # (Agent Framework doesn't support dynamic tool addition after creation)
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        chat_client = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=self.model,
            credential=DefaultAzureCredential(),
        )
        
        self.agent = chat_client.create_agent(
            name=self.name,
            instructions=self.instructions,
            tools=new_tools,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
    
    @property
    def id(self) -> str:
        """Get the agent's unique ID."""
        return self.agent.id
    
    @property
    def display_name(self) -> str:
        """Get the agent's display name."""
        return self.agent.display_name
    
    async def serialize_thread(self, thread: AgentThread, **kwargs: Any) -> dict[str, Any]:
        """
        Serialize a thread to a dictionary for storage.
        
        Args:
            thread: The thread to serialize
            **kwargs: Additional arguments for serialization
            
        Returns:
            Dictionary containing serialized thread state
        """
        return await thread.serialize(**kwargs)
    
    async def deserialize_thread(self, serialized_thread: dict[str, Any], **kwargs: Any) -> AgentThread:
        """
        Deserialize a thread from its serialized state.
        
        Args:
            serialized_thread: The serialized thread data
            **kwargs: Additional arguments for deserialization
            
        Returns:
            A restored AgentThread instance
        """
        return await self.agent.deserialize_thread(serialized_thread, **kwargs)
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"DemoBaseAgent(name='{self.name}', id='{self.id}', model='{self.model}')"
