"""
Step Repository
CRUD operations for execution steps/traces in Cosmos DB.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional
from azure.cosmos import exceptions

from src.persistence.cosmos_client import get_cosmos
from src.persistence.models import Step, StepStatus, StepType, ToolCall, Message

logger = logging.getLogger(__name__)

CONTAINER_NAME = "steps"


class StepRepository:
    """Repository for managing execution steps in Cosmos DB."""
    
    def __init__(self):
        """Initialize step repository."""
        self.cosmos = get_cosmos()
        if not self.cosmos:
            logger.error("Cosmos DB client not initialized")
            raise RuntimeError("Cosmos DB client not available")
        
        self.container = self.cosmos.get_container(CONTAINER_NAME)
    
    async def create(
        self,
        run_id: str,
        thread_id: str,
        agent_id: str,
        step_type: StepType,
        tool_call: Optional[ToolCall] = None,
        message: Optional[Message] = None
    ) -> Step:
        """
        Create a new step.
        
        Args:
            run_id: Parent run ID
            thread_id: Parent thread ID
            agent_id: Agent ID
            step_type: Type of step
            tool_call: Optional tool call details
            message: Optional message details
            
        Returns:
            Created Step object
        """
        step_id = f"step_{uuid.uuid4().hex[:12]}"
        
        step = Step(
            id=step_id,
            run_id=run_id,
            thread_id=thread_id,
            agent_id=agent_id,
            step_type=step_type,
            status=StepStatus.IN_PROGRESS,
            tool_call=tool_call,
            message=message,
            started_at=datetime.utcnow()
        )
        
        try:
            # Insert into Cosmos DB
            item = step.model_dump(by_alias=True, exclude_none=True, mode='json')
            self.container.create_item(body=item)
            
            logger.debug(f"Created step {step_id} for run {run_id}")
            return step
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error creating step: {str(e)}")
            raise
    
    async def get(self, step_id: str) -> Optional[Step]:
        """
        Get a step by ID.
        
        Args:
            step_id: Step ID
            
        Returns:
            Step object or None if not found
        """
        try:
            item = self.container.read_item(
                item=step_id,
                partition_key=step_id
            )
            return Step(**item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Step {step_id} not found")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error getting step {step_id}: {str(e)}")
            raise
    
    async def list_by_run(
        self,
        run_id: str,
        limit: int = 100
    ) -> List[Step]:
        """
        List steps for a specific run.
        
        Args:
            run_id: Run ID
            limit: Maximum number of steps to return
            
        Returns:
            List of Step objects in chronological order
        """
        try:
            query = f"""
                SELECT * FROM c
                WHERE c.run_id = '{run_id}'
                ORDER BY c.started_at ASC
                OFFSET 0 ROWS
                FETCH NEXT {limit} ROWS ONLY
            """
            
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            steps = [Step(**item) for item in items]
            logger.debug(f"Listed {len(steps)} steps for run {run_id}")
            
            return steps
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error listing steps for run {run_id}: {str(e)}")
            raise
    
    async def list_by_thread(
        self,
        thread_id: str,
        limit: int = 200
    ) -> List[Step]:
        """
        List steps for a specific thread.
        
        Args:
            thread_id: Thread ID
            limit: Maximum number of steps to return
            
        Returns:
            List of Step objects in chronological order
        """
        try:
            query = f"""
                SELECT * FROM c
                WHERE c.thread_id = '{thread_id}'
                ORDER BY c.started_at DESC
                OFFSET 0 ROWS
                FETCH NEXT {limit} ROWS ONLY
            """
            
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            steps = [Step(**item) for item in items]
            logger.debug(f"Listed {len(steps)} steps for thread {thread_id}")
            
            return steps
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error listing steps for thread {thread_id}: {str(e)}")
            raise
    
    async def update(self, step: Step) -> Step:
        """
        Update an existing step.
        
        Args:
            step: Step object with updates
            
        Returns:
            Updated Step object
        """
        try:
            item = step.model_dump(by_alias=True, exclude_none=True, mode='json')
            
            # Use etag for optimistic concurrency if available
            options = {}
            if step.etag:
                options['if_match'] = step.etag
            
            updated_item = self.container.replace_item(
                item=step.id,
                body=item,
                **options
            )
            
            logger.debug(f"Updated step {step.id}")
            return Step(**updated_item)
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error updating step {step.id}: {str(e)}")
            raise
    
    async def complete_step(
        self,
        step_id: str,
        status: StepStatus = StepStatus.COMPLETED,
        error: Optional[str] = None
    ) -> Step:
        """
        Mark a step as completed (or failed).
        
        Args:
            step_id: Step ID
            status: Final status (completed or failed)
            error: Optional error message
            
        Returns:
            Updated Step object
        """
        step = await self.get(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")
        
        step.status = status
        step.completed_at = datetime.utcnow()
        
        if error:
            step.error = error
        
        # Update tool call status if applicable
        if step.tool_call:
            step.tool_call.status = status
            step.tool_call.completed_at = datetime.utcnow()
            
            if error:
                step.tool_call.error = error
            
            # Calculate latency
            if step.started_at and step.completed_at:
                delta = step.completed_at - step.started_at
                step.tool_call.latency_ms = int(delta.total_seconds() * 1000)
        
        return await self.update(step)
    
    async def update_tool_call_output(
        self,
        step_id: str,
        output: dict,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None
    ) -> Step:
        """
        Update tool call output and token usage.
        
        Args:
            step_id: Step ID
            output: Tool output data
            tokens_input: Optional input tokens
            tokens_output: Optional output tokens
            
        Returns:
            Updated Step object
        """
        step = await self.get(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")
        
        if not step.tool_call:
            raise ValueError(f"Step {step_id} is not a tool call")
        
        step.tool_call.output = output
        
        if tokens_input is not None:
            step.tool_call.tokens_input = tokens_input
        if tokens_output is not None:
            step.tool_call.tokens_output = tokens_output
        if tokens_input is not None and tokens_output is not None:
            step.tool_call.tokens_total = tokens_input + tokens_output
        
        return await self.update(step)


# Singleton instance
_step_repository: Optional[StepRepository] = None


def get_step_repository() -> StepRepository:
    """Get or create the step repository singleton."""
    global _step_repository
    if _step_repository is None:
        _step_repository = StepRepository()
    return _step_repository
