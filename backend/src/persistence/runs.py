"""
Run Repository
CRUD operations for agent runs in Cosmos DB.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional
from azure.cosmos import exceptions

from src.persistence.cosmos_client import get_cosmos
from src.persistence.models import Run, RunStatus

logger = logging.getLogger(__name__)

CONTAINER_NAME = "runs"


class RunRepository:
    """Repository for managing agent runs in Cosmos DB."""
    
    def __init__(self):
        """Initialize run repository."""
        self.cosmos = get_cosmos()
        if not self.cosmos:
            logger.error("Cosmos DB client not initialized")
            raise RuntimeError("Cosmos DB client not available")
        
        self.container = self.cosmos.get_container(CONTAINER_NAME)
    
    async def create(
        self,
        thread_id: str,
        agent_id: str,
        user_message_id: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Run:
        """
        Create a new agent run.
        
        Args:
            thread_id: Parent thread ID
            agent_id: Agent ID
            user_message_id: ID of the user message that triggered this run
            model: Model name (e.g., gpt-4o)
            temperature: Model temperature
            max_tokens: Max tokens for response
            
        Returns:
            Created Run object
        """
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        run = Run(
            id=run_id,
            thread_id=thread_id,
            agent_id=agent_id,
            status=RunStatus.QUEUED,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            user_message_id=user_message_id,
            steps=[],
            created_at=datetime.utcnow(),
            tokens_input=0,
            tokens_output=0,
            tokens_total=0
        )
        
        try:
            # Insert into Cosmos DB
            item = run.model_dump(by_alias=True, exclude_none=True, mode='json')
            self.container.create_item(body=item)
            
            logger.info(f"Created run {run_id} for thread {thread_id}")
            return run
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error creating run: {str(e)}")
            raise
    
    async def get(self, run_id: str, thread_id: str) -> Optional[Run]:
        """
        Get a run by ID.
        
        Args:
            run_id: Run ID
            thread_id: Thread ID (required for partition key)
            
        Returns:
            Run object or None if not found
        """
        try:
            item = self.container.read_item(
                item=run_id,
                partition_key=thread_id
            )
            return Run(**item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Run {run_id} not found")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error getting run {run_id}: {str(e)}")
            raise
    
    async def list_by_thread(
        self,
        thread_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Run]:
        """
        List runs for a specific thread.
        
        Args:
            thread_id: Thread ID
            limit: Maximum number of runs to return
            offset: Number of runs to skip
            
        Returns:
            List of Run objects
        """
        try:
            query = f"""
                SELECT * FROM c
                WHERE c.thread_id = '{thread_id}'
                ORDER BY c.created_at DESC
                OFFSET {offset}
                LIMIT {limit}
            """
            
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            runs = [Run(**item) for item in items]
            logger.debug(f"Listed {len(runs)} runs for thread {thread_id}")
            
            return runs
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error listing runs for thread {thread_id}: {str(e)}")
            raise
    
    async def update(self, run: Run) -> Run:
        """
        Update an existing run.
        
        Args:
            run: Run object with updates
            
        Returns:
            Updated Run object
        """
        try:
            item = run.model_dump(by_alias=True, exclude_none=True, mode='json')
            
            # Use etag for optimistic concurrency if available
            options = {}
            if run.etag:
                options['if_match'] = run.etag
            
            updated_item = self.container.replace_item(
                item=run.id,
                body=item,
                **options
            )
            
            logger.debug(f"Updated run {run.id}")
            return Run(**updated_item)
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error updating run {run.id}: {str(e)}")
            raise
    
    async def update_status(self, run_id: str, thread_id: str, status: RunStatus, error: Optional[str] = None, run: Optional['Run'] = None) -> Run:
        """
        Update run status.
        
        Args:
            run_id: Run ID
            thread_id: Thread ID (required for partition key)
            status: New status
            error: Optional error message
            run: Optional Run object (if provided, skip retrieval)
            
        Returns:
            Updated Run object
        """
        if run is None:
            run = await self.get(run_id, thread_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")
        
        run.status = status
        
        if status == RunStatus.IN_PROGRESS and not run.started_at:
            run.started_at = datetime.utcnow()
        elif status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
            run.completed_at = datetime.utcnow()
        
        if error:
            run.error = error
        
        return await self.update(run)
    
    async def add_step(self, run_id: str, thread_id: str, step_id: str) -> Run:
        """
        Add a step ID to a run's step list.
        
        Args:
            run_id: Run ID
            thread_id: Thread ID (required for partition key)
            step_id: Step ID to add
            
        Returns:
            Updated Run object
        """
        run = await self.get(run_id, thread_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        run.steps.append(step_id)
        return await self.update(run)
    
    async def update_tokens(
        self,
        run_id: str,
        thread_id: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: Optional[float] = None,
        run: Optional['Run'] = None
    ) -> Run:
        """
        Update token usage for a run.
        
        Args:
            run_id: Run ID
            thread_id: Thread ID (required for partition key)
            tokens_input: Input tokens used
            tokens_output: Output tokens used
            cost_usd: Optional cost in USD
            run: Optional Run object (if provided, skip retrieval)
            
        Returns:
            Updated Run object
        """
        if run is None:
            run = await self.get(run_id, thread_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")
        
        run.tokens_input += tokens_input
        run.tokens_output += tokens_output
        run.tokens_total = run.tokens_input + run.tokens_output
        
        if cost_usd is not None:
            run.cost_usd = (run.cost_usd or 0.0) + cost_usd
        
        return await self.update(run)
    
    async def set_assistant_message(self, run_id: str, thread_id: str, message_id: str, run: Optional['Run'] = None) -> Run:
        """
        Set the assistant message ID for a run.
        
        Args:
            run_id: Run ID
            thread_id: Thread ID (required for partition key)
            message_id: Assistant message ID
            run: Optional Run object (if provided, skip retrieval)
            
        Returns:
            Updated Run object
        """
        if run is None:
            run = await self.get(run_id, thread_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")
        
        run.assistant_message_id = message_id
        return await self.update(run)


# Singleton instance
_run_repository: Optional[RunRepository] = None


def get_run_repository() -> RunRepository:
    """Get or create the run repository singleton."""
    global _run_repository
    if _run_repository is None:
        _run_repository = RunRepository()
    return _run_repository
