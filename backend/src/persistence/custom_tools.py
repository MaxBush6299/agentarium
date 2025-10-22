"""
Custom Tools Repository for managing custom MCP tools in Cosmos DB.

This repository handles CRUD operations for custom tools, including:
- Creating and retrieving custom tools
- Listing all custom tools
- Updating custom tool configuration
- Deleting custom tools

Uses the 'agents' collection with a 'custom_tool' type marker to avoid creating a new collection.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict
from azure.cosmos import exceptions

from src.persistence.cosmos_client import get_cosmos
from src.api.custom_tools import CustomToolConfig

logger = logging.getLogger(__name__)

CONTAINER_NAME = "agents"  # Reuse existing agents collection


class CustomToolsRepository:
    """Repository for managing custom tools metadata using the agents collection."""
    
    def __init__(self):
        """Initialize the custom tools repository."""
        self.cosmos = get_cosmos()
        if not self.cosmos:
            logger.error("Cosmos DB client not initialized")
            raise RuntimeError("Cosmos DB client not available")
        
        self.container = self.cosmos.get_container(CONTAINER_NAME)
    
    def upsert(self, tool: CustomToolConfig) -> CustomToolConfig:
        """
        Upsert (create or update) a custom tool in the database.
        Stores it in the agents collection with type='custom_tool' marker.
        
        Args:
            tool: Custom tool configuration to upsert
        Returns:
            Upserted tool with Cosmos DB fields populated
        """
        try:
            # Prepare document for Cosmos DB
            # Use the tool ID as partition key (which is /id in agents collection)
            doc = {
                "id": tool.id,
                "type": "custom_tool",  # Type marker to distinguish from agents
                "name": tool.name,
                "description": tool.description,
                "url": tool.url,
                "auth_type": tool.auth_type.value,
                "oauth_config": tool.oauth_config.dict() if tool.oauth_config else None,
                "apikey_config": tool.apikey_config.dict() if tool.apikey_config else None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            result = self.container.upsert_item(doc)
            logger.info(f"✓ Upserted custom tool: {tool.id} ({tool.name})")
            return tool
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to upsert custom tool {tool.id}: {e}")
            raise
    
    def get_by_id(self, tool_id: str) -> Optional[CustomToolConfig]:
        """
        Retrieve a custom tool by ID.
        
        Args:
            tool_id: ID of the tool
        Returns:
            CustomToolConfig if found, None otherwise
        """
        try:
            result = self.container.read_item(item=tool_id, partition_key=tool_id)
            return self._to_custom_tool_config(result)
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Custom tool not found: {tool_id}")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to retrieve custom tool {tool_id}: {e}")
            return None
    
    def list_all(self) -> List[CustomToolConfig]:
        """
        List all custom tools.
        
        Returns:
            List of all custom tool configurations
        """
        try:
            query = "SELECT * FROM c WHERE c.type = 'custom_tool' ORDER BY c.created_at DESC"
            results = self.container.query_items(query=query, enable_cross_partition_query=True)
            tools = []
            for doc in results:
                tool = self._to_custom_tool_config(doc)
                if tool:
                    tools.append(tool)
            logger.debug(f"Retrieved {len(tools)} custom tools from database")
            return tools
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to list custom tools: {e}")
            return []
    
    def delete(self, tool_id: str) -> bool:
        """
        Delete a custom tool by ID.
        
        Args:
            tool_id: ID of the tool to delete
        Returns:
            True if deleted, False if not found or error
        """
        try:
            self.container.delete_item(item=tool_id, partition_key=tool_id)
            logger.info(f"✓ Deleted custom tool: {tool_id}")
            return True
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Custom tool not found for deletion: {tool_id}")
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to delete custom tool {tool_id}: {e}")
            return False
    
    def _to_custom_tool_config(self, doc: Dict) -> Optional[CustomToolConfig]:
        """
        Convert Cosmos DB document to CustomToolConfig.
        
        Args:
            doc: Cosmos DB document
        Returns:
            CustomToolConfig or None if conversion fails
        """
        try:
            from src.api.custom_tools import AuthType, OAuthConfig, ApiKeyConfig
            
            # Reconstruct auth config objects
            oauth_config = None
            if doc.get("oauth_config"):
                oauth_config = OAuthConfig(**doc["oauth_config"])
            
            apikey_config = None
            if doc.get("apikey_config"):
                apikey_config = ApiKeyConfig(**doc["apikey_config"])
            
            return CustomToolConfig(
                id=doc["id"],
                name=doc["name"],
                description=doc["description"],
                url=doc["url"],
                auth_type=AuthType(doc.get("auth_type", "none")),
                oauth_config=oauth_config,
                apikey_config=apikey_config,
            )
        except Exception as e:
            logger.error(f"Failed to convert document to CustomToolConfig: {e}")
            return None


def get_custom_tools_repository() -> CustomToolsRepository:
    """Get the custom tools repository instance."""
    return CustomToolsRepository()

