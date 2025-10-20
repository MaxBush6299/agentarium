"""Azure Operations Assistant Agent Implementation.

This module implements the Azure Ops Assistant Agent, which specializes in
Azure resource management, monitoring, and deployment operations.

The agent uses:
- Azure MCP tool for resource discovery and log analysis  
- Ops Assistant OpenAPI tool for deployment operations
- GPT-4o model for intelligent Azure operations guidance
"""

import logging
from typing import Optional

from .base import DemoBaseAgent
from ..tools.mcp_tools import get_azure_mcp_tool
from ..tools.openapi_client import get_ops_assistant_tool

logger = logging.getLogger(__name__)


# Azure Ops Assistant Agent system prompt
AZURE_OPS_SYSTEM_PROMPT = """You are an Azure operations assistant with deep expertise in Azure cloud infrastructure and DevOps practices.

Your primary responsibilities:
1. **Discover and manage Azure resources** across subscriptions and resource groups
2. **Monitor resource health and performance** using Azure metrics and diagnostics
3. **Analyze logs and troubleshoot issues** in Azure services
4. **Manage deployments** and track deployment history
5. **Provide recommendations** for optimization, cost savings, and best practices

When responding:
- Always verify resource names, IDs, and subscription context before operations
- Provide structured information about resource properties and status
- Summarize key findings from logs, highlighting errors and warnings
- Use proper Azure terminology (Resource Groups, Subscriptions, ARM, etc.)
- Suggest actionable next steps for troubleshooting or optimization
- Be proactive about identifying potential security or performance issues

Available tools:
- **Azure MCP**: List resources, get resource details, query Azure Monitor logs
- **Ops Assistant API**: Check deployment status, view deployment history, rollback deployments

Response format:
- Start with a clear summary of what you found
- Show resource details in a structured, readable format
- Highlight any warnings, errors, or anomalies  
- End with actionable recommendations or next steps

Remember: You have read-only access for most operations. For write operations (deployments, updates), use the Ops Assistant API or provide clear guidance on required Azure CLI/Portal steps."""


class AzureOpsAgent:
    """
    Azure Operations Assistant Agent for Azure resource management and operations.
    
    This agent specializes in:
    - Azure resource discovery and monitoring
    - Log analysis and troubleshooting
    - Deployment management and history
    - Azure best practices and recommendations
    
    Attributes:
        base_agent (DemoBaseAgent): Underlying agent implementation
        name (str): Agent display name
        
    Example:
        ```python
        # Create agent
        agent = AzureOpsAgent.create()
        
        # Get a new conversation thread
        thread = agent.get_new_thread()
        
        # Run agent with a query
        response = await agent.run(
            "List all Container Apps in the production resource group",
            thread=thread
        )
        print(response.messages[-1].content)
        
        # Check deployment status
        response = await agent.run(
            "What is the current deployment status?",
            thread=thread
        )
        ```
    """
    
    def __init__(self, base_agent: DemoBaseAgent):
        """
        Initialize Azure Ops Agent with a base agent.
        
        Args:
            base_agent: Configured DemoBaseAgent instance with tools
        """
        self.base_agent = base_agent
        self.name = "Azure Ops Assistant"
        logger.info(f"Initialized {self.name}")
    
    @classmethod
    def create(
        cls,
        model: str = "gpt-4o",
        max_messages: int = 20,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        azure_mcp_url: Optional[str] = None,
        ops_api_base_url: Optional[str] = None,
        ops_api_key: Optional[str] = None
    ) -> "AzureOpsAgent":
        """
        Create a new Azure Ops Agent with default configuration.
        
        This factory method creates a fully configured agent with:
        - Azure MCP tool for resource discovery and log analysis
        - Ops Assistant OpenAPI tool for deployment operations
        - Optimized system prompt for Azure operations
        - Sliding window memory (20 messages default)
        
        Args:
            model: Azure OpenAI model deployment name (default: "gpt-4o")
            max_messages: Maximum messages in sliding window (default: 20)
            temperature: Model temperature for response generation (default: 0.7)
            max_tokens: Maximum tokens per response (default: None)
            azure_mcp_url: Custom Azure MCP endpoint (default: None, uses env AZURE_MCP_URL)
            ops_api_base_url: Custom Ops Assistant API base URL (default: None, uses env OPS_API_URL)
            ops_api_key: Custom API key for Ops Assistant API (default: None, uses env OPS_API_KEY)
            
        Returns:
            AzureOpsAgent: Configured agent instance
            
        Raises:
            ValueError: If agent creation fails or no tools can be configured
            ConnectionError: If tools cannot be initialized
            
        Example:
            ```python
            # Create with defaults
            agent = AzureOpsAgent.create()
            
            # Create with custom configuration
            agent = AzureOpsAgent.create(
                model="gpt-4",
                max_messages=30,
                temperature=0.5
            )
            ```
        """
        logger.info("Creating Azure Ops Assistant Agent")
        
        # Create tools
        tools = []
        
        try:
            # Azure MCP tool
            azure_mcp = get_azure_mcp_tool(server_url=azure_mcp_url)
            tools.append(azure_mcp)
            logger.info("Azure MCP tool initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Azure MCP tool: {e}")
            # Continue - agent can work with just OpenAPI tool
        
        try:
            # Ops Assistant OpenAPI tool
            ops_tool = get_ops_assistant_tool(
                base_url=ops_api_base_url,
                api_key=ops_api_key
            )
            tools.append(ops_tool)
            logger.info("Ops Assistant API tool initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Ops Assistant API tool: {e}")
            # Continue if we have at least one tool
        
        if not tools:
            error_msg = "Failed to initialize any tools for Azure Ops Agent"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create base agent with tools
        base_agent = DemoBaseAgent(
            name="Azure Ops Assistant",
            instructions=AZURE_OPS_SYSTEM_PROMPT,
            tools=tools,
            model=model,
            max_messages=max_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        logger.info(f"Azure Ops Agent created with model={model}, {len(tools)} tool(s)")
        
        # Wrap in AzureOpsAgent
        return cls(base_agent)
    
    # Delegate core methods to base_agent
    
    async def run(self, *args, **kwargs):
        """Run the agent. Delegates to base_agent.run()."""
        return await self.base_agent.run(*args, **kwargs)
    
    async def run_stream(self, *args, **kwargs):
        """Stream agent responses. Delegates to base_agent.run_stream()."""
        async for update in self.base_agent.run_stream(*args, **kwargs):
            yield update
    
    def get_new_thread(self, **kwargs):
        """Create a new conversation thread. Delegates to base_agent."""
        return self.base_agent.get_new_thread(**kwargs)
    
    # Convenience methods for common Azure operations
    
    async def list_resources(
        self,
        resource_group: Optional[str] = None,
        resource_type: Optional[str] = None,
        thread=None
    ):
        """
        Convenience method to list Azure resources.
        
        Args:
            resource_group: Optional resource group name to filter
            resource_type: Optional resource type (e.g., "Microsoft.Web/sites")
            thread: Optional conversation thread
            
        Returns:
            Agent response with resource list
        """
        query = "List Azure resources"
        
        if resource_group:
            query += f" in resource group '{resource_group}'"
        
        if resource_type:
            query += f" of type '{resource_type}'"
        
        return await self.run(query, thread=thread)
    
    async def get_deployment_status(self, environment: str = "production", thread=None):
        """
        Convenience method to check deployment status.
        
        Args:
            environment: Environment name (production, staging, dev)
            thread: Optional conversation thread
            
        Returns:
            Agent response with deployment status
        """
        return await self.run(
            f"What is the current deployment status for {environment}?",
            thread=thread
        )
    
    async def analyze_logs(
        self,
        resource_name: str,
        time_range: str = "last 1 hour",
        thread=None
    ):
        """
        Convenience method to analyze resource logs.
        
        Args:
            resource_name: Name of the Azure resource
            time_range: Time range for logs (e.g., "last 1 hour", "last 24 hours")
            thread: Optional conversation thread
            
        Returns:
            Agent response with log analysis
        """
        return await self.run(
            f"Analyze logs for {resource_name} from {time_range}. "
            "Summarize any errors, warnings, or unusual patterns.",
            thread=thread
        )

