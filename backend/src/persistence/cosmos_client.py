"""
Azure Cosmos DB client wrapper and initialization.
Provides convenient access to Cosmos DB with proper connection handling and retry policies.
"""

import logging
from typing import Optional
from azure.cosmos import CosmosClient, errors
from azure.cosmos.partition_key import PartitionKey

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """
    Wrapper around Azure Cosmos DB Python SDK.
    Handles connection, database, and container management.
    """
    
    def __init__(
        self,
        endpoint: str,
        database_name: str,
        key: Optional[str] = None,
        connection_string: Optional[str] = None,
    ):
        """
        Initialize Cosmos DB client.
        
        Args:
            endpoint: Cosmos DB endpoint URL
            database_name: Name of the database
            key: Primary key for authentication (if using key auth)
            connection_string: Connection string (if using connection string auth)
        """
        self.endpoint = endpoint
        self.database_name = database_name
        self.client: Optional[CosmosClient] = None
        self.database = None
        self.containers: dict = {}
        
        try:
            # Initialize client based on provided credentials
            if connection_string:
                self.client = CosmosClient.from_connection_string(connection_string)
                logger.info("CosmosDB client initialized with connection string")
            elif key:
                try:
                    self.client = CosmosClient(endpoint, credential=key)
                    logger.info(f"CosmosDB client initialized with key auth to {endpoint}")
                except Exception as key_error:
                    # If key auth fails (e.g., local auth disabled), fall back to managed identity
                    logger.warning(f"Key auth failed: {key_error}. Trying managed identity...")
                    from azure.identity import DefaultAzureCredential
                    credential = DefaultAzureCredential()
                    self.client = CosmosClient(endpoint, credential=credential)
                    logger.info(f"CosmosDB client initialized with managed identity to {endpoint}")
            else:
                # For managed identity, DefaultAzureCredential is used
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                self.client = CosmosClient(endpoint, credential=credential)
                logger.info(f"CosmosDB client initialized with managed identity to {endpoint}")
            
            # Get database reference
            self.database = self.client.get_database_client(database_name)
            logger.info(f"Connected to database: {database_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB client: {str(e)}")
            raise
    
    def get_container(self, container_name: str):
        """
        Get a container reference, caching it for reuse.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Container client instance
        """
        if container_name not in self.containers:
            try:
                self.containers[container_name] = self.database.get_container_client(container_name)
                logger.debug(f"Loaded container reference: {container_name}")
            except Exception as e:
                logger.error(f"Error getting container {container_name}: {str(e)}")
                raise
        
        return self.containers[container_name]
    
    def query_items(self, container_name: str, query: str, parameters: Optional[list] = None):
        """
        Query items from a container.
        
        Args:
            container_name: Name of the container
            query: SQL query string
            parameters: Query parameters
            
        Returns:
            Iterator of items matching the query
        """
        container = self.get_container(container_name)
        try:
            return container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            )
        except Exception as e:
            logger.error(f"Error querying container {container_name}: {str(e)}")
            raise
    
    def create_item(self, container_name: str, body: dict):
        """
        Create a new item in a container.
        
        Args:
            container_name: Name of the container
            body: Item data (must include 'id' and partition key)
            
        Returns:
            The created item
        """
        container = self.get_container(container_name)
        try:
            return container.create_item(body=body)
        except errors.CosmosResourceExistsError:
            logger.warning(f"Item with id {body.get('id')} already exists in {container_name}")
            raise
        except Exception as e:
            logger.error(f"Error creating item in {container_name}: {str(e)}")
            raise
    
    def read_item(self, container_name: str, item_id: str, partition_key: str):
        """
        Read a single item from a container.
        
        Args:
            container_name: Name of the container
            item_id: ID of the item
            partition_key: Partition key value
            
        Returns:
            The item if found, None otherwise
        """
        container = self.get_container(container_name)
        try:
            return container.read_item(item=item_id, partition_key=partition_key)
        except errors.CosmosResourceNotFoundError:
            logger.debug(f"Item {item_id} not found in {container_name}")
            return None
        except Exception as e:
            logger.error(f"Error reading item {item_id} from {container_name}: {str(e)}")
            raise
    
    def update_item(self, container_name: str, item_id: str, body: dict):
        """
        Update an existing item in a container.
        
        Args:
            container_name: Name of the container
            item_id: ID of the item
            body: Updated item data (must include 'id' and partition key)
            
        Returns:
            The updated item
        """
        container = self.get_container(container_name)
        try:
            return container.replace_item(item=item_id, body=body)
        except errors.CosmosResourceNotFoundError:
            logger.error(f"Item {item_id} not found in {container_name}")
            raise
        except Exception as e:
            logger.error(f"Error updating item {item_id} in {container_name}: {str(e)}")
            raise
    
    def delete_item(self, container_name: str, item_id: str, partition_key: str):
        """
        Delete an item from a container.
        
        Args:
            container_name: Name of the container
            item_id: ID of the item
            partition_key: Partition key value
        """
        container = self.get_container(container_name)
        try:
            container.delete_item(item=item_id, partition_key=partition_key)
            logger.debug(f"Deleted item {item_id} from {container_name}")
        except errors.CosmosResourceNotFoundError:
            logger.warning(f"Item {item_id} not found in {container_name}")
        except Exception as e:
            logger.error(f"Error deleting item {item_id} from {container_name}: {str(e)}")
            raise
    
    def health_check(self) -> bool:
        """
        Perform a health check on the Cosmos DB connection.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Try to read database properties
            _ = self.database.read()
            logger.info("Cosmos DB health check passed")
            return True
        except Exception as e:
            logger.error(f"Cosmos DB health check failed: {str(e)}")
            return False


# Global Cosmos DB client instance
_cosmos_client: Optional[CosmosDBClient] = None


def initialize_cosmos(
    endpoint: str,
    database_name: str,
    key: Optional[str] = None,
    connection_string: Optional[str] = None,
) -> CosmosDBClient:
    """
    Initialize the global Cosmos DB client.
    
    Args:
        endpoint: Cosmos DB endpoint URL
        database_name: Name of the database
        key: Primary key for authentication
        connection_string: Connection string
        
    Returns:
        The initialized CosmosDBClient instance
    """
    global _cosmos_client
    _cosmos_client = CosmosDBClient(endpoint, database_name, key, connection_string)
    return _cosmos_client


def get_cosmos() -> Optional[CosmosDBClient]:
    """
    Get the global Cosmos DB client instance.
    Returns None if not initialized.
    """
    return _cosmos_client
