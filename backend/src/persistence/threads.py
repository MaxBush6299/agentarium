"""
Thread Repository
CRUD operations for conversation threads in Cosmos DB.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from azure.cosmos import exceptions

from src.persistence.cosmos_client import get_cosmos
from src.persistence.models import Thread, Message

logger = logging.getLogger(__name__)

CONTAINER_NAME = "threads"

# Thread pool for running blocking Cosmos DB operations
_executor = ThreadPoolExecutor(max_workers=5)


class ThreadRepository:
    """Repository for managing conversation threads in Cosmos DB."""
    
    def __init__(self):
        """Initialize thread repository."""
        self.cosmos = get_cosmos()
        if not self.cosmos:
            logger.error("Cosmos DB client not initialized")
            raise RuntimeError("Cosmos DB client not available")
        
        self.container = self.cosmos.get_container(CONTAINER_NAME)
    
    async def create(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Thread:
        """
        Create a new conversation thread.
        
        Args:
            agent_id: ID of the agent for this thread
            user_id: Optional user ID
            workflow_id: Optional workflow ID if thread is part of a multi-agent workflow
            metadata: Optional metadata dictionary
            
        Returns:
            Created Thread object
        """
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        
        thread = Thread(
            id=thread_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            user_id=user_id,
            messages=[],
            runs=[],
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        try:
            # Insert into Cosmos DB (blocking operation)
            item = thread.model_dump(by_alias=True, exclude_none=True, mode='json')
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(_executor, lambda: self.container.create_item(body=item))
            
            logger.info(f"Created thread {thread_id} for agent {agent_id}")
            return thread
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error creating thread: {str(e)}")
            raise
    
    async def get(self, thread_id: str, agent_id: str) -> Optional[Thread]:
        """
        Get a thread by ID.
        
        Args:
            thread_id: Thread ID
            agent_id: Agent ID (required for partition key)
            
        Returns:
            Thread object or None if not found
        """
        try:
            loop = asyncio.get_event_loop()
            logger.debug(f"Attempting to read thread {thread_id} with partition key {agent_id}")
            item = await loop.run_in_executor(
                _executor,
                lambda: self.container.read_item(
                    item=thread_id,
                    partition_key=agent_id
                )
            )
            logger.debug(f"Successfully read thread {thread_id}: {item}")
            return Thread(**item)
            
        except exceptions.CosmosResourceNotFoundError as e:
            logger.warning(f"Thread {thread_id} not found with agent_id {agent_id}: {str(e)}")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error getting thread {thread_id}: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting thread {thread_id}: {str(e)}", exc_info=True)
            raise
    
    async def list(
        self,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: str = "active",
        limit: int = 50,
        offset: int = 0
    ) -> List[Thread]:
        """
        List threads with optional filtering.
        
        Args:
            agent_id: Filter by agent ID
            user_id: Filter by user ID
            status: Filter by status (default: active)
            limit: Maximum number of threads to return
            offset: Number of threads to skip
            
        Returns:
            List of Thread objects
        """
        try:
            # Build query
            conditions = [f"c.status = '{status}'"]
            
            if agent_id:
                conditions.append(f"c.agentId = '{agent_id}'")
            if user_id:
                conditions.append(f"c.user_id = '{user_id}'")
            
            where_clause = " AND ".join(conditions)
            # Cosmos DB uses TOP and OFFSET (not FETCH NEXT ROWS ONLY like SQL Server)
            query = f"""
                SELECT * FROM c
                WHERE {where_clause}
                ORDER BY c.updated_at DESC
                OFFSET {offset}
                LIMIT {limit}
            """
            
            loop = asyncio.get_event_loop()
            items = await loop.run_in_executor(
                _executor,
                lambda: list(self.container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            )
            
            threads = [Thread(**item) for item in items]
            logger.debug(f"Listed {len(threads)} threads (agent_id={agent_id}, user_id={user_id})")
            
            return threads
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error listing threads: {str(e)}")
            raise
    
    async def update(self, thread: Thread) -> Thread:
        """
        Update an existing thread.
        
        Args:
            thread: Thread object with updates
            
        Returns:
            Updated Thread object
        """
        try:
            thread.updated_at = datetime.utcnow()
            
            item = thread.model_dump(by_alias=True, exclude_none=True, mode='json')
            
            # Use etag for optimistic concurrency if available
            options = {}
            if thread.etag:
                options['if_match'] = thread.etag
            
            loop = asyncio.get_event_loop()
            updated_item = await loop.run_in_executor(
                _executor,
                lambda: self.container.replace_item(
                    item=thread.id,
                    body=item,
                    **options
                )
            )
            
            logger.info(f"Updated thread {thread.id}")
            return Thread(**updated_item)
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error updating thread {thread.id}: {str(e)}")
            raise
    
    async def add_message(self, thread_id: str, agent_id: str, message: Message, thread: Optional[Thread] = None) -> Thread:
        """
        Add a message to a thread.
        
        Args:
            thread_id: Thread ID
            agent_id: Agent ID (required for partition key)
            message: Message object to add
            thread: Optional Thread object (if not provided, will fetch from DB)
            
        Returns:
            Updated Thread object
        """
        if not thread:
            thread = await self.get(thread_id, agent_id)
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")
        
        # Add message to thread
        thread.messages.append(message)
        
        # Auto-generate title from first user message if not set
        if not thread.title and message.role == "user" and len(thread.messages) == 1:
            # Use first 50 chars of message as title
            thread.title = message.content[:50] + ("..." if len(message.content) > 50 else "")
        
        return await self.update(thread)
    
    async def add_run(self, thread_id: str, agent_id: str, run_id: str, thread: Optional[Thread] = None) -> Thread:
        """
        Add a run ID to a thread's run history.
        
        Args:
            thread_id: Thread ID
            agent_id: Agent ID (required for partition key)
            run_id: Run ID to add
            thread: Optional Thread object (if not provided, will fetch from DB)
            
        Returns:
            Updated Thread object
        """
        if not thread:
            thread = await self.get(thread_id, agent_id)
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")
        
        thread.runs.append(run_id)
        return await self.update(thread)
    
    async def delete(self, thread_id: str, agent_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a thread (soft or hard delete).
        Idempotent operation - returns True even if thread doesn't exist.
        
        Args:
            thread_id: Thread ID
            agent_id: Agent ID (required for partition key)
            soft_delete: If True, mark as deleted; if False, actually delete
            
        Returns:
            True if successful (or thread didn't exist)
        """
        try:
            if soft_delete:
                thread = await self.get(thread_id, agent_id)
                if thread:
                    thread.status = "deleted"
                    await self.update(thread)
                    logger.info(f"Soft deleted thread {thread_id}")
                else:
                    logger.info(f"Thread {thread_id} not found (idempotent delete)")
            else:
                loop = asyncio.get_event_loop()
                try:
                    await loop.run_in_executor(
                        _executor,
                        lambda: self.container.delete_item(
                            item=thread_id,
                            partition_key=agent_id
                        )
                    )
                    logger.info(f"Hard deleted thread {thread_id}")
                except exceptions.CosmosResourceNotFoundError:
                    logger.info(f"Thread {thread_id} not found (idempotent delete)")
            
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error deleting thread {thread_id}: {str(e)}")
            raise
    
    async def count(
        self,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: str = "active"
    ) -> int:
        """
        Count threads with optional filtering.
        
        Args:
            agent_id: Filter by agent ID
            user_id: Filter by user ID
            status: Filter by status
            
        Returns:
            Count of threads
        """
        try:
            conditions = [f"c.status = '{status}'"]
            
            if agent_id:
                conditions.append(f"c.agent_id = '{agent_id}'")
            if user_id:
                conditions.append(f"c.user_id = '{user_id}'")
            
            where_clause = " AND ".join(conditions)
            query = f"SELECT VALUE COUNT(1) FROM c WHERE {where_clause}"
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                lambda: list(self.container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            )
            
            return result[0] if result else 0
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error counting threads: {str(e)}")
            raise


# Singleton instance
_thread_repository: Optional[ThreadRepository] = None


def get_thread_repository() -> ThreadRepository:
    """Get or create the thread repository singleton."""
    global _thread_repository
    if _thread_repository is None:
        _thread_repository = ThreadRepository()
    return _thread_repository
