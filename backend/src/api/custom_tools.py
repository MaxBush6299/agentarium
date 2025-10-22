"""
Custom Tools API

Provides REST endpoints for registering and managing custom MCP servers.
Allows users to dynamically add custom MCP tools without code changes.

Endpoints:
- POST /api/custom-tools - Register a new custom MCP tool
- GET /api/custom-tools - List all registered custom tools
- DELETE /api/custom-tools/{tool_id} - Unregister a custom tool
"""

import logging
import json
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Store custom tools in memory (loaded from Cosmos DB on startup)
_custom_tools: Dict[str, "CustomToolConfig"] = {}


class AuthType(str, Enum):
    """Supported authentication types for MCP servers"""
    NONE = "none"
    APIKEY = "apikey"
    OAUTH = "oauth"


class OAuthConfig(BaseModel):
    """OAuth 2.0 configuration for custom MCP tools"""
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    token_url: str = Field(..., description="OAuth token endpoint URL")
    scope: Optional[str] = Field(
        default="api://default/.default",
        description="OAuth scope"
    )


class ApiKeyConfig(BaseModel):
    """API Key configuration for custom MCP tools"""
    api_key: str = Field(..., description="API key for authentication")


class CustomToolConfig(BaseModel):
    """Configuration for a custom MCP tool"""
    id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Display name for the tool")
    description: str = Field(..., description="Description of what the tool does")
    url: str = Field(..., description="URL of the MCP server endpoint")
    auth_type: AuthType = Field(
        default=AuthType.NONE,
        description="Authentication type: none, apikey, or oauth"
    )
    oauth_config: Optional[OAuthConfig] = Field(
        default=None,
        description="OAuth configuration (required if auth_type=oauth)"
    )
    apikey_config: Optional[ApiKeyConfig] = Field(
        default=None,
        description="API Key configuration (required if auth_type=apikey)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when tool was registered"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "adventure-works-001",
                "name": "Adventure Works Database",
                "description": "Query the Adventure Works sample database",
                "url": "https://mssqlmcp.azure-api.net/mcp",
                "auth_type": "oauth",
                "oauth_config": {
                    "client_id": "17a97781-0078-4478-8b4e-fe5dda9e2400",
                    "client_secret": "Kyb8Q~FL6eva5m6pbe...",
                    "token_url": "https://login.microsoftonline.com/.../oauth2/v2.0/token",
                    "scope": "api://17a97781-0078-4478-8b4e-fe5dda9e2400/.default"
                },
                "created_at": "2025-10-22T15:30:00"
            }
        }


class CustomToolCreateRequest(BaseModel):
    """Request to register a new custom MCP tool"""
    name: str = Field(..., description="Display name for the tool")
    description: str = Field(..., description="Description of what the tool does")
    url: str = Field(..., description="URL of the MCP server endpoint")
    auth_type: AuthType = Field(
        default=AuthType.NONE,
        description="Authentication type: none, apikey, or oauth"
    )
    oauth_config: Optional[OAuthConfig] = Field(
        default=None,
        description="OAuth configuration (required if auth_type=oauth)"
    )
    apikey_config: Optional[ApiKeyConfig] = Field(
        default=None,
        description="API Key configuration (required if auth_type=apikey)"
    )


class CustomToolResponse(BaseModel):
    """Response model for custom tool endpoints"""
    id: str
    name: str
    description: str
    url: str
    auth_type: AuthType
    has_oauth_config: bool  # Don't expose secrets in response
    has_apikey_config: bool  # Don't expose secrets in response
    created_at: datetime


class CustomToolListResponse(BaseModel):
    """Response for listing custom tools"""
    tools: List[CustomToolResponse]
    total: int


# Create router
router = APIRouter(prefix="/api/custom-tools", tags=["custom-tools"])


def _custom_tool_to_response(config: CustomToolConfig) -> CustomToolResponse:
    """Convert CustomToolConfig to response (without secrets)"""
    return CustomToolResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        url=config.url,
        auth_type=config.auth_type,
        has_oauth_config=config.oauth_config is not None,
        has_apikey_config=config.apikey_config is not None,
        created_at=config.created_at,
    )


@router.post(
    "",
    response_model=CustomToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new custom MCP tool",
    description="Register a custom MCP server that can be used with agents"
)
async def register_custom_tool(request: CustomToolCreateRequest) -> CustomToolResponse:
    """
    Register a new custom MCP tool.
    
    Validates the configuration and stores it for later use.
    The tool can then be selected when configuring agents.
    
    Args:
        request: Custom tool configuration
        
    Returns:
        Registered custom tool (without secrets)
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 409: If tool with same name already exists
    """
    import uuid
    
    # Validate auth configuration
    if request.auth_type == AuthType.OAUTH and not request.oauth_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="oauth_config is required when auth_type is 'oauth'"
        )
    
    if request.auth_type == AuthType.APIKEY and not request.apikey_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="apikey_config is required when auth_type is 'apikey'"
        )
    
    # Check for duplicate names
    for tool in _custom_tools.values():
        if tool.name.lower() == request.name.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Custom tool with name '{request.name}' already exists"
            )
    
    # Create new tool config
    tool_id = f"custom-{uuid.uuid4().hex[:8]}"
    config = CustomToolConfig(
        id=tool_id,
        name=request.name,
        description=request.description,
        url=request.url,
        auth_type=request.auth_type,
        oauth_config=request.oauth_config,
        apikey_config=request.apikey_config,
    )
    
    # Store in memory
    _custom_tools[tool_id] = config
    
    # Persist to Cosmos DB
    try:
        from src.persistence.custom_tools import get_custom_tools_repository
        repo = get_custom_tools_repository()
        repo.upsert(config)
        logger.info(f"✓ Persisted custom tool to Cosmos DB: {config.name} ({tool_id})")
    except Exception as e:
        logger.warning(f"Failed to persist custom tool to Cosmos DB: {e}")
    
    # Register in tool registry so agents can use it
    try:
        from src.agents.tool_registry import get_tool_registry, ToolDefinition
        from src.tools.mcp_tools import get_custom_mcp_tool
        
        registry = get_tool_registry()
        
        # Create factory function for this custom tool
        # IMPORTANT: Use default parameters to capture values by reference, not by name
        # This prevents closure bugs where 'config' gets reassigned by later registrations
        def custom_tool_factory(
            cfg: dict,
            _tool_name: str = config.name,
            _tool_url: str = config.url,
            _auth_type: str = config.auth_type.value,
            _api_key: Optional[str] = config.apikey_config.api_key if config.apikey_config else None,
            _client_id: Optional[str] = config.oauth_config.client_id if config.oauth_config else None,
            _client_secret: Optional[str] = config.oauth_config.client_secret if config.oauth_config else None,
            _token_url: Optional[str] = config.oauth_config.token_url if config.oauth_config else None,
            _scope: Optional[str] = config.oauth_config.scope if config.oauth_config else None,
        ) -> object:
            return get_custom_mcp_tool(
                name=_tool_name,
                url=_tool_url,
                auth_type=_auth_type,
                api_key=_api_key,
                client_id=_client_id,
                client_secret=_client_secret,
                token_url=_token_url,
                scope=_scope,
            )
        
        # Register the tool
        registry.register(ToolDefinition(
            type="mcp",
            name=tool_id,
            description=request.description,
            factory=custom_tool_factory,
            required_config={},
            optional_config={}
        ))
        
        logger.info(f"✓ Registered custom MCP tool in registry: {config.name} ({tool_id})")
    except Exception as e:
        logger.warning(f"Failed to register custom tool in registry: {e}")
    
    logger.info(f"Registered custom MCP tool: {config.name} ({tool_id})")
    
    return _custom_tool_to_response(config)


@router.get(
    "",
    response_model=CustomToolListResponse,
    summary="List all custom MCP tools",
    description="Get list of all registered custom MCP tools"
)
async def list_custom_tools() -> CustomToolListResponse:
    """
    List all registered custom MCP tools.
    
    Returns a list of all custom tools that have been registered.
    Secrets (API keys, OAuth credentials) are not included in the response.
    
    Returns:
        List of custom tools
    """
    tools = [_custom_tool_to_response(config) for config in _custom_tools.values()]
    return CustomToolListResponse(tools=tools, total=len(tools))


@router.get(
    "/{tool_id}",
    response_model=CustomToolResponse,
    summary="Get custom MCP tool details",
    description="Get details for a specific custom MCP tool"
)
async def get_custom_tool(tool_id: str) -> CustomToolResponse:
    """
    Get details for a specific custom MCP tool.
    
    Args:
        tool_id: ID of the custom tool
        
    Returns:
        Custom tool details (without secrets)
        
    Raises:
        HTTPException 404: If tool not found
    """
    if tool_id not in _custom_tools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom tool '{tool_id}' not found"
        )
    
    return _custom_tool_to_response(_custom_tools[tool_id])


@router.delete(
    "/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister a custom MCP tool",
    description="Remove a registered custom MCP tool"
)
async def delete_custom_tool(tool_id: str) -> None:
    """
    Unregister a custom MCP tool.
    
    Args:
        tool_id: ID of the custom tool to remove
        
    Raises:
        HTTPException 404: If tool not found
    """
    if tool_id not in _custom_tools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom tool '{tool_id}' not found"
        )
    
    tool_name = _custom_tools[tool_id].name
    del _custom_tools[tool_id]
    
    # Delete from Cosmos DB
    try:
        from src.persistence.custom_tools import get_custom_tools_repository
        repo = get_custom_tools_repository()
        repo.delete(tool_id)
        logger.info(f"✓ Deleted custom tool from Cosmos DB: {tool_name} ({tool_id})")
    except Exception as e:
        logger.warning(f"Failed to delete custom tool from Cosmos DB: {e}")
    
    logger.info(f"Unregistered custom MCP tool: {tool_name} ({tool_id})")


def get_custom_tool_config(tool_id: str) -> Optional[CustomToolConfig]:
    """
    Retrieve custom tool configuration by ID.
    
    Used internally by agents to load tool credentials for instantiation.
    
    Args:
        tool_id: ID of the custom tool
        
    Returns:
        CustomToolConfig if found, None otherwise
    """
    return _custom_tools.get(tool_id)


def get_all_custom_tools() -> Dict[str, CustomToolConfig]:
    """
    Retrieve all custom tool configurations.
    
    Used internally to list available custom tools.
    
    Returns:
        Dictionary of all custom tool configurations
    """
    return _custom_tools.copy()


async def load_custom_tools_from_db():
    """
    Load all custom tools from Cosmos DB into memory cache.
    
    Called on startup to restore persisted custom tools.
    """
    global _custom_tools
    
    try:
        from src.persistence.custom_tools import get_custom_tools_repository
        
        repo = get_custom_tools_repository()
        tools = repo.list_all()
        
        _custom_tools.clear()
        for tool in tools:
            _custom_tools[tool.id] = tool
            
            # Also register in tool registry
            try:
                from src.agents.tool_registry import get_tool_registry, ToolDefinition
                from src.tools.mcp_tools import get_custom_mcp_tool
                
                registry = get_tool_registry()
                
                # Create factory function for this custom tool
                def make_factory(cfg_tool: CustomToolConfig):
                    def custom_tool_factory(cfg: dict):
                        return get_custom_mcp_tool(
                            name=cfg_tool.name,
                            url=cfg_tool.url,
                            auth_type=cfg_tool.auth_type.value,
                            api_key=cfg_tool.apikey_config.api_key if cfg_tool.apikey_config else None,
                            client_id=cfg_tool.oauth_config.client_id if cfg_tool.oauth_config else None,
                            client_secret=cfg_tool.oauth_config.client_secret if cfg_tool.oauth_config else None,
                            token_url=cfg_tool.oauth_config.token_url if cfg_tool.oauth_config else None,
                            scope=cfg_tool.oauth_config.scope if cfg_tool.oauth_config else None,
                        )
                    return custom_tool_factory
                
                # Register the tool
                registry.register(ToolDefinition(
                    type="mcp",
                    name=tool.id,
                    description=tool.description,
                    factory=make_factory(tool),
                    required_config={},
                    optional_config={}
                ))
                logger.debug(f"✓ Registered custom tool in registry on startup: {tool.name} ({tool.id})")
            except Exception as e:
                logger.debug(f"Failed to register custom tool in registry on startup: {e}")
        
        logger.info(f"✓ Loaded {len(tools)} custom tools from Cosmos DB on startup")
    except Exception as e:
        logger.warning(f"Failed to load custom tools from Cosmos DB on startup: {e}")
        # Continue anyway - empty custom tools list is fine

