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
        
        print(f"[AGENT_INIT] Initializing DemoBaseAgent:")
        print(f"  - name: {name}")
        print(f"  - model: {model}")
        print(f"  - tools provided: {len(tools) if tools else 0}")
        if tools:
            for i, tool in enumerate(tools):
                print(f"    [{i}] {type(tool).__name__}: {tool}")
        import sys
        sys.stdout.flush()
        
        # Initialize Azure OpenAI client with credentials
        from src.config import settings
        
        endpoint = settings.AZURE_OPENAI_ENDPOINT
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
        
        logger.info(f"Initializing agent '{name}' with model '{model}'")
        
        # Map model name to Azure deployment name if needed
        deployment_name = settings.MODEL_DEPLOYMENT_MAPPING.get(model, model)
        print(f"[AGENT_INIT] Model '{model}' mapped to deployment '{deployment_name}'")
        
        # Prepare credential and api_key for Azure OpenAI client
        credential = None
        api_key = None
        
        if settings.AZURE_OPENAI_KEY:
            # Use API key authentication
            api_key = settings.AZURE_OPENAI_KEY
            logger.debug("Using API key authentication for Azure OpenAI")
            print(f"[AGENT_INIT] Using API key: {api_key[:20]}...")
        else:
            # Use managed identity/default credentials
            credential = DefaultAzureCredential()
            logger.debug("Using DefaultAzureCredential for Azure OpenAI")
            print(f"[AGENT_INIT] Using DefaultAzureCredential")
        
        print(f"[AGENT_INIT] Creating AzureOpenAIResponsesClient with:")
        print(f"  - endpoint: {endpoint}")
        print(f"  - deployment_name: {deployment_name}")
        print(f"  - api_version: {settings.AZURE_OPENAI_API_VERSION}")
        print(f"  - credential: {credential}")
        print(f"  - api_key: {'<set>' if api_key else '<not set>'}")
        sys.stdout.flush()
        
        # Create the ChatAgent using Azure OpenAI Responses client
        chat_client = AzureOpenAIResponsesClient(
            endpoint=endpoint,
            deployment_name=deployment_name,
            credential=credential,
            api_key=api_key,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        
        print(f"[AGENT_INIT] AzureOpenAIResponsesClient created: {chat_client}")
        sys.stdout.flush()
        
        # Create the ChatAgent with tools
        print(f"[AGENT_INIT] About to create_agent with {len(tools) if tools else 0} tools")
        sys.stdout.flush()
        self.agent = chat_client.create_agent(
            name=name,
            instructions=instructions,
            tools=tools if tools else [],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        print(f"[AGENT_INIT] ChatAgent created: {self.agent}")
        sys.stdout.flush()
        
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
        print(f"[{self.name.upper()}_RUN] Starting agent run")
        import sys
        sys.stdout.flush()
        
        # Run the agent
        response = await self.agent.run(
            messages=message,
            thread=thread,
            tool_choice="required",  # Force tool usage when tools are available
            **kwargs
        )
        
        logger.debug(f"Agent '{self.name}' completed response")
        
        # Log any tool calls made by this agent
        if hasattr(response, 'messages') and response.messages:
            self._log_tool_calls_from_response(response, self.name)
        
        return response
    
    def _log_tool_calls_from_response(self, response: AgentRunResponse, agent_name: str):
        """
        Extract and log tool calls from agent response.
        
        This captures tool invocations made by the agent and logs them
        for debugging and observability.
        
        Args:
            response: AgentRunResponse from agent.run()
            agent_name: Name of the agent for logging context
        """
        import json
        import sys
        
        tool_count = 0
        
        for i, msg in enumerate(response.messages):
            msg_role = getattr(msg, 'role', None)
            
            # Convert Role enum to string if needed
            if msg_role and hasattr(msg_role, 'value'):
                role_str = str(msg_role.value)
            else:
                role_str = str(msg_role) if msg_role else 'unknown'
            
            # Look for tool calls (either in 'tool' role or in assistant message contents)
            if role_str == 'tool':
                # This is a tool result message
                tool_count += 1
                try:
                    msg_vars = vars(msg)
                    tool_name = 'unknown_tool'
                    result_preview = ""
                    
                    # Extract tool details from contents
                    if 'contents' in msg_vars and msg_vars['contents']:
                        for content_item in msg_vars['contents']:
                            content_vars = vars(content_item)
                            
                            # Get call_id as tool identifier
                            if 'call_id' in content_vars:
                                tool_name = str(content_vars['call_id'])
                            
                            # Extract result if available
                            if 'result' in content_vars and isinstance(content_vars['result'], list):
                                result_texts = []
                                for result_item in content_vars['result']:
                                    result_vars = vars(result_item)
                                    if 'text' in result_vars:
                                        result_texts.append(result_vars['text'])
                                if result_texts:
                                    result_preview = '\n'.join(result_texts)[:100]
                    
                    print(f"[{agent_name.upper()}_TOOL_CALL] Tool: {tool_name}")
                    if result_preview:
                        print(f"[{agent_name.upper()}_TOOL_RESULT] {result_preview}...")
                    
                except Exception as e:
                    print(f"[{agent_name.upper()}_TOOL_CALL_LOG_ERROR] Error logging: {e}")
            
            elif role_str == 'assistant':
                # Check assistant message for tool use blocks
                try:
                    msg_vars = vars(msg)
                    if 'contents' in msg_vars and msg_vars['contents']:
                        for content_item in msg_vars['contents']:
                            content_vars = vars(content_item)
                            content_type = type(content_item).__name__
                            
                            # Look for FunctionCallContent or similar
                            if 'name' in content_vars and content_vars['name']:
                                tool_count += 1
                                tool_name = content_vars['name']
                                args_preview = ""
                                
                                if 'arguments' in content_vars:
                                    args_preview = str(content_vars['arguments'])[:50]
                                
                                print(f"[{agent_name.upper()}_TOOL_INVOKED] Tool: {tool_name}")
                                if args_preview:
                                    print(f"[{agent_name.upper()}_TOOL_ARGS] {args_preview}...")
                
                except Exception as e:
                    pass
        
        if tool_count > 0:
            print(f"[{agent_name.upper()}_RUN] Completed with {tool_count} tool call(s)")
        
        sys.stdout.flush()
    
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
        print(f"[BASE.run_stream.1] Starting run_stream, about to call self.agent.run_stream()")
        print(f"[BASE.run_stream.1a] Message type: {type(message)}, length: {len(str(message))}")
        print(f"[BASE.run_stream.1b] Thread: {thread}")
        print(f"[BASE.run_stream.1c] self.agent type: {type(self.agent)}")
        import sys
        sys.stdout.flush()
        
        # Stream the agent response
        print(f"[BASE.run_stream.2] About to enter async for loop on self.agent.run_stream()")
        sys.stdout.flush()
        async for update in self.agent.run_stream(
            messages=message,
            thread=thread,
            **kwargs
        ):
            print(f"[BASE.run_stream.3] Got update from agent: {type(update).__name__}")
            yield update
        print(f"[BASE.run_stream.4] Stream completed")
    
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
