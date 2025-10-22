"""
Agent Repository for managing agent metadata in Cosmos DB.

This repository handles CRUD operations for agents, including:
- Creating and retrieving agents
- Listing agents with filtering
- Updating agent configuration and statistics
- Activating/deactivating agents
- Soft deletion (via status change)
"""
import logging
from datetime import datetime
from typing import List, Optional
from azure.cosmos import exceptions

from src.persistence.cosmos_client import get_cosmos
from .models import AgentMetadata, AgentStatus, ToolConfig, AgentUpdateRequest

logger = logging.getLogger(__name__)

CONTAINER_NAME = "agents"


class AgentRepository:
    """Repository for managing agent metadata."""
    
    def __init__(self):
        """Initialize the agent repository."""
        self.cosmos = get_cosmos()
        if not self.cosmos:
            logger.error("Cosmos DB client not initialized")
            raise RuntimeError("Cosmos DB client not available")
        
        self.container = self.cosmos.get_container(CONTAINER_NAME)
    
    def upsert(self, agent: AgentMetadata) -> AgentMetadata:
        """
        Upsert (create or update) an agent in the database.
        Uses Cosmos DB's upsert_item to avoid 409 Conflict errors.
        
        Args:
            agent: Agent metadata to upsert
        Returns:
            Upserted agent with Cosmos DB fields populated
        """
        # Ensure timestamps are set
        if not agent.created_at:
            agent.created_at = datetime.utcnow()
        agent.updated_at = datetime.utcnow()
        
        agent_dict = agent.model_dump(by_alias=True, mode='json')
        try:
            result = self.container.upsert_item(body=agent_dict)
            logger.info(f"Upserted agent: {agent.id}")
            agent.etag = result.get("_etag")
            return agent
        except Exception as e:
            logger.error(f"Failed to upsert agent {agent.id}: {e}")
            raise
    
    def get(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get an agent by ID.
        
        Uses query_items instead of read_item to avoid eventual consistency issues.
        query_items performs a fresh database query while read_item uses cached data.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent metadata or None if not found
        """
        try:
            # Use query_items for fresh database query (better consistency)
            query = "SELECT * FROM c WHERE c.id = @id"
            parameters = [{"name": "@id", "value": agent_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                logger.debug(f"Agent not found: {agent_id}")
                return None
            
            result = items[0]
            
            # Convert from Cosmos DB format
            if "_etag" in result:
                result["etag"] = result.pop("_etag")
            
            agent = AgentMetadata(**result)
            logger.debug(f"Retrieved agent: {agent_id}")
            return agent
                    
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise
    
    def list(
        self,
        status: Optional[AgentStatus] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AgentMetadata]:
        """
        List agents with optional filtering.
        
        Args:
            status: Filter by status (active, inactive, maintenance)
            is_public: Filter by visibility
            limit: Maximum number of agents to return
            offset: Number of agents to skip
            
        Returns:
            List of agent metadata
        """
        # Build query
        query = "SELECT * FROM c WHERE 1=1"
        parameters = []
        
        if status is not None:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        if is_public is not None:
            query += " AND c.is_public = @is_public"
            parameters.append({"name": "@is_public", "value": is_public})
        
        query += " ORDER BY c.created_at DESC"
        query += f" OFFSET {offset} LIMIT {limit}"
        
        try:
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )
            
            agents = []
            for item in items:
                # Convert from Cosmos DB format
                if "_etag" in item:
                    item["etag"] = item.pop("_etag")
                agents.append(AgentMetadata(**item))
            
            logger.debug(f"Listed {len(agents)} agents (status={status}, is_public={is_public})")
            return agents
            
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise
    
    def count(
        self,
        status: Optional[AgentStatus] = None,
        is_public: Optional[bool] = None
    ) -> int:
        """
        Count agents with optional filtering.
        
        Args:
            status: Filter by status
            is_public: Filter by visibility
            
        Returns:
            Number of matching agents
        """
        # Build query
        query = "SELECT VALUE COUNT(1) FROM c WHERE 1=1"
        parameters = []
        
        if status is not None:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        if is_public is not None:
            query += " AND c.is_public = @is_public"
            parameters.append({"name": "@is_public", "value": is_public})
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # COUNT returns a single integer value
            return items[0] if items else 0
            
        except Exception as e:
            logger.error(f"Failed to count agents: {e}")
            raise
    
    def update(
        self,
        agent_id: str,
        updates: AgentUpdateRequest,
        etag: Optional[str] = None
    ) -> Optional[AgentMetadata]:
        """
        Update an agent's configuration.
        
        Args:
            agent_id: Agent identifier
            updates: Fields to update (only non-None fields are updated)
            etag: Optional etag for optimistic concurrency
            
        Returns:
            Updated agent or None if not found
            
        Raises:
            exceptions.CosmosHttpResponseError: If etag doesn't match (concurrent update)
        """
        # Get current agent
        agent = self.get(agent_id)
        if not agent:
            return None
        
        # Apply updates (only non-None fields)
        update_dict = updates.model_dump(exclude_none=True)
        for key, value in update_dict.items():
            setattr(agent, key, value)
        
        # Update timestamp
        agent.updated_at = datetime.utcnow()
        
        # Convert to dict for Cosmos DB
        agent_dict = agent.model_dump(by_alias=True, mode='json')
        
        try:
            # Use etag for optimistic concurrency if provided
            options = {}
            if etag:
                options["if_match"] = etag
            
            result = self.container.replace_item(
                item=agent_id,
                body=agent_dict,
                **options
            )
            
            logger.info(f"Updated agent: {agent_id}")
            
            # Update with new etag
            agent.etag = result.get("_etag")
            return agent
            
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Agent not found for update: {agent_id}")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise
    
    def delete(self, agent_id: str, hard_delete: bool = False) -> bool:
        """
        Delete an agent (soft delete by default).
        
        Args:
            agent_id: Agent identifier
            hard_delete: If True, permanently delete. If False, set status to inactive.
            
        Returns:
            True if deleted, False if not found
        """
        if hard_delete:
            # Permanently delete from Cosmos DB
            try:
                self.container.delete_item(
                    item=agent_id,
                    partition_key=agent_id
                )
                logger.info(f"Hard deleted agent: {agent_id}")
                return True
                
            except exceptions.CosmosResourceNotFoundError:
                logger.debug(f"Agent not found for deletion: {agent_id}")
                return False
            except Exception as e:
                logger.error(f"Failed to delete agent {agent_id}: {e}")
                raise
        else:
            # Soft delete: set status to inactive
            agent = self.get(agent_id)
            if not agent:
                return False
            
            updates = AgentUpdateRequest(status=AgentStatus.INACTIVE)
            self.update(agent_id, updates)
            logger.info(f"Soft deleted agent (set to inactive): {agent_id}")
            return True
    
    def update_stats(
        self,
        agent_id: str,
        tokens_used: int,
        latency_ms: float
    ) -> bool:
        """
        Update agent usage statistics after a run.
        
        Args:
            agent_id: Agent identifier
            tokens_used: Number of tokens used in the run
            latency_ms: Response latency in milliseconds
            
        Returns:
            True if updated, False if agent not found
        """
        agent = self.get(agent_id)
        if not agent:
            return False
        
        # Update statistics
        agent.total_runs += 1
        agent.total_tokens += tokens_used
        
        # Update average latency (incremental average)
        if agent.avg_latency_ms is None:
            agent.avg_latency_ms = latency_ms
        else:
            # Weighted average: (old_avg * old_count + new_value) / new_count
            old_total = agent.avg_latency_ms * (agent.total_runs - 1)
            agent.avg_latency_ms = (old_total + latency_ms) / agent.total_runs
        
        agent.last_used_at = datetime.utcnow()
        agent.updated_at = datetime.utcnow()
        
        # Save to database
        agent_dict = agent.model_dump(by_alias=True, mode='json')
        
        try:
            result = self.container.replace_item(
                item=agent_id,
                body=agent_dict
            )
            
            logger.debug(f"Updated stats for agent {agent_id}: runs={agent.total_runs}, tokens={agent.total_tokens}")
            agent.etag = result.get("_etag")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update stats for agent {agent_id}: {e}")
            raise
    
    def activate(self, agent_id: str) -> bool:
        """
        Activate an agent (set status to ACTIVE).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if activated, False if not found
        """
        updates = AgentUpdateRequest(status=AgentStatus.ACTIVE)
        agent = self.update(agent_id, updates)
        
        if agent:
            logger.info(f"Activated agent: {agent_id}")
            return True
        return False
    
    def deactivate(self, agent_id: str) -> bool:
        """
        Deactivate an agent (set status to INACTIVE).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if deactivated, False if not found
        """
        updates = AgentUpdateRequest(status=AgentStatus.INACTIVE)
        agent = self.update(agent_id, updates)
        
        if agent:
            logger.info(f"Deactivated agent: {agent_id}")
            return True
        return False


# Singleton instance
_agent_repository: Optional[AgentRepository] = None


def get_agent_repository() -> AgentRepository:
    """
    Get the singleton agent repository instance.
    
    Returns:
        AgentRepository instance
        
    Raises:
        RuntimeError: If Cosmos client is not initialized
    """
    global _agent_repository
    
    if _agent_repository is None:
        print("[DEBUG agents.py] Initializing AgentRepository singleton...")
        _agent_repository = AgentRepository()
        print(f"[DEBUG agents.py] AgentRepository initialized: {_agent_repository}")
    else:
        print(f"[DEBUG agents.py] Returning existing AgentRepository: {_agent_repository}")
    
    return _agent_repository

