"""
Workflows API Router

RESTful API endpoints for multi-agent workflow orchestration.
Supports:
1. Listing available workflows
2. Executing workflows with SSE streaming
"""

import asyncio
import json
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path, Body
from fastapi.responses import StreamingResponse

from src.persistence.models import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


@router.get("", name="list_workflows")
async def list_workflows():
    """
    Get all available workflows with metadata.
    
    Returns a dictionary mapping workflow IDs to their configurations:
    - id: Unique workflow identifier
    - name: Display name
    - description: Workflow description
    - status: Workflow status (active/inactive based on 'active' field)
    - associatedAgents: List of participant agents
    - type: Workflow pattern (handoff, sequential, parallel, approval_chain)
    - coordinator: Primary coordinator agent
    - metadata: Additional workflow information
    
    Example Response:
        {
            "intelligent-handoff": {
                "id": "intelligent-handoff",
                "name": "Intelligent Handoff",
                "description": "Multi-tier routing with evaluation",
                "status": "ACTIVE",
                "associatedAgents": ["router", "data-agent", "analyst", ...],
                "type": "handoff",
                "coordinator": "router",
                ...
            },
            ...
        }
    """
    try:
        logger.info("[WORKFLOWS] Starting list_workflows()")
        from src.agents.workflows import get_available_workflows
        
        logger.info("[WORKFLOWS] get_available_workflows imported successfully")
        workflows = get_available_workflows()
        logger.info(f"[WORKFLOWS] Returning {len(workflows)} available workflows")
        
        # Transform workflow configs to frontend format
        transformed_workflows = {}
        for workflow_id, config in workflows.items():
            transformed_workflows[workflow_id] = {
                "id": config.get("id"),
                "name": config.get("name"),
                "description": config.get("description"),
                "type": config.get("type"),
                "status": "ACTIVE" if config.get("active", False) else "INACTIVE",
                "associatedAgents": config.get("participants", []),
                "coordinator": config.get("coordinator"),
                "metadata": config.get("metadata", {}),
                "routing_rules": config.get("routing_rules", {}),
            }
        
        if transformed_workflows:
            logger.info(f"[WORKFLOWS] Workflow IDs: {list(transformed_workflows.keys())}")
        
        return transformed_workflows
        
    except ImportError as e:
        logger.error(f"[WORKFLOWS] Failed to import workflows module: {str(e)}", exc_info=True)
        # Graceful degradation - return empty dict if workflows module unavailable
        return {}
    except Exception as e:
        logger.error(f"[WORKFLOWS] Error listing workflows: {str(e)}", exc_info=True)
        # Return empty dict instead of error to prevent frontend breaking
        return {}


@router.post("/{workflow_id}/chat", name="execute_workflow")
async def execute_workflow(
    workflow_id: str = Path(..., description="Workflow ID to execute"),
    request: Optional[ChatRequest] = None
):
    """
    Execute a workflow with streaming response.
    
    The workflow coordinator manages agent interactions and routing.
    Response is streamed as SSE events:
    1. status: Workflow starting
    2. trace events: Agent interactions and handoffs
    3. message: Final response
    4. metadata: Handoff path, satisfaction score, evaluator reasoning
    5. done: Stream complete
    
    Args:
        workflow_id: ID of the workflow to execute
        request: Chat request with message, thread_id, etc.
    
    Returns:
        StreamingResponse with SSE events:
        1. Status event (workflow starting)
        2. Trace events (agent invocations)
        3. Message event (final response)
        4. Metadata event (handoff path, satisfaction score)
        5. Done event
    
    Example Request:
        {
            "message": "Show me top customers and provide business insights",
            "thread_id": "thread-xyz123",
            "max_handoffs": 3
        }
    
    TODO: Implement workflow execution
    Current: Placeholder returning mock response
    """
    if request is None:
        raise HTTPException(status_code=400, detail="Request body required")
    
    try:
        from src.agents.workflows import validate_workflow_id, get_workflow_config
        
        logger.info(f"Workflow chat request: workflow={workflow_id}, thread={request.thread_id}")
        
        # Validate workflow exists
        if not validate_workflow_id(workflow_id):
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        
        workflow_config = get_workflow_config(workflow_id)
        if workflow_config is None:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' configuration not found")
        
        logger.info(f"Workflow type: {workflow_config.get('type')}")
        
        # Execute the appropriate workflow
        async def event_generator():
            """Generate SSE events for workflow execution."""
            try:
                # Status event
                yield f"event: status\ndata: {json.dumps({'status': 'workflow_starting', 'workflow_id': workflow_id})}\n\n"
                await asyncio.sleep(0.1)
                
                # Execute based on workflow type
                workflow_type = workflow_config.get('type', '')
                
                if workflow_type == 'handoff':
                    # Import and execute handoff orchestrator
                    from src.agents.workflows.handoff_orchestrator import HandoffOrchestrator
                    
                    # Create orchestrator with required parameters
                    thread_id = request.thread_id or f"thread-{workflow_id}"
                    orchestrator = HandoffOrchestrator(
                        workflow_id=workflow_id,
                        workflow_config=workflow_config
                    )
                    
                    # Execute workflow
                    final_response, trace_metadata = await orchestrator.execute(
                        message=request.message,
                        thread_id=thread_id
                    )
                    
                    logger.info(f"Handoff workflow complete: path={trace_metadata.handoff_path}")
                    
                    # Message event with final response
                    yield f"event: message\ndata: {json.dumps({'message': final_response})}\n\n"
                    await asyncio.sleep(0.1)
                    
                    # Metadata event with trace
                    metadata_dict = {
                        'workflow_id': workflow_id,
                        'thread_id': thread_id,
                        'handoff_path': trace_metadata.handoff_path,
                        'total_handoffs': trace_metadata.total_handoffs,
                        'final_satisfaction_score': trace_metadata.final_satisfaction_score,
                        'final_evaluator_reasoning': trace_metadata.final_evaluator_reasoning,
                        'max_attempts_reached': trace_metadata.max_attempts_reached,
                    }
                    yield f"event: metadata\ndata: {json.dumps(metadata_dict)}\n\n"
                    await asyncio.sleep(0.1)
                
                elif workflow_type == 'sequential':
                    # Import and execute sequential orchestrator
                    from src.agents.workflows.sequential_orchestrator import SequentialOrchestrator
                    
                    logger.info("Starting sequential workflow execution...")
                    
                    # Create orchestrator with required parameters
                    thread_id = request.thread_id or f"thread-{workflow_id}"
                    orchestrator = SequentialOrchestrator(
                        workflow_id=workflow_id,
                        workflow_config=workflow_config
                    )
                    
                    logger.info("Orchestrator created, calling execute()...")
                    
                    # Execute workflow
                    try:
                        final_response, trace_metadata = await orchestrator.execute(
                            message=request.message,
                            thread_id=thread_id
                        )
                    except Exception as e:
                        logger.error(f"Sequential workflow execution error: {e}", exc_info=True)
                        raise
                    
                    logger.info(f"Sequential workflow complete: response_length={len(final_response)}")
                    
                    # Message event with final response
                    yield f"event: message\ndata: {json.dumps({'message': final_response})}\n\n"
                    await asyncio.sleep(0.1)
                    
                    # Metadata event with trace
                    metadata_dict = {
                        'workflow_id': workflow_id,
                        'thread_id': thread_id,
                        'workflow_type': workflow_type,
                        'pattern': 'Sequential Pipeline',
                        'execution_path': 'data-agent → analyst',
                    }
                    yield f"event: metadata\ndata: {json.dumps(metadata_dict)}\n\n"
                    await asyncio.sleep(0.1)
                
                else:
                    # Unknown workflow type
                    yield f"event: message\ndata: {json.dumps({'message': f'Workflow type {workflow_type} not yet implemented'})}\n\n"
                yield f"event: done\ndata: {json.dumps({'complete': True})}\n\n"
            
            except Exception as e:
                logger.error(f"Error in workflow event generator: {str(e)}", exc_info=True)
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                yield f"event: done\ndata: {json.dumps({'complete': False})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/threads", name="create_workflow_thread")
async def create_workflow_thread(
    workflow_id: str = Path(..., description="Workflow ID"),
    request: Optional[dict] = Body(None)
):
    """
    Create a new chat thread for workflow execution.
    
    Args:
        workflow_id: ID of the workflow
        request: Optional request body with title
        
    Returns:
        New thread object with empty messages
    """
    try:
        from src.persistence.threads import get_thread_repository
        
        repo = get_thread_repository()
        title = request.get("title") if request else None
        
        thread = await repo.create(
            agent_id=workflow_id,
            workflow_id=workflow_id,
            title=title,
            metadata={"workflow_type": "workflow"}
        )
        
        logger.info(f"Created workflow thread: {thread.id}")
        
        return {
            "id": thread.id,
            "agent_id": thread.agent_id,
            "title": thread.title or "Untitled",
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "messages": [],
        }
        
    except Exception as e:
        logger.error(f"Error creating workflow thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/threads", name="list_workflow_threads")
async def list_workflow_threads(
    workflow_id: str = Path(..., description="Workflow ID"),
    limit: int = 50
):
    """
    List all threads for a workflow.
    
    Args:
        workflow_id: ID of the workflow
        limit: Maximum threads to return
        
    Returns:
        Dictionary with threads list and metadata
    """
    try:
        from src.persistence.threads import get_thread_repository
        
        repo = get_thread_repository()
        threads = await repo.list(agent_id=workflow_id, limit=limit)
        
        logger.info(f"Found {len(threads)} threads for workflow {workflow_id}")
        
        return {
            "threads": [
                {
                    "id": t.id,
                    "agent_id": t.agent_id,
                    "title": t.title or "Untitled",
                    "created_at": t.created_at.isoformat(),
                    "updated_at": t.updated_at.isoformat(),
                    "messages": [],  # Don't include full message history in list
                }
                for t in threads
            ],
            "total": len(threads),
            "page": 1,
            "page_size": limit,
        }
        
    except Exception as e:
        logger.error(f"Error listing workflow threads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/threads/{thread_id}", name="get_workflow_thread")
async def get_workflow_thread(
    workflow_id: str = Path(..., description="Workflow ID"),
    thread_id: str = Path(..., description="Thread ID")
):
    """
    Get workflow thread details including messages.
    
    Args:
        workflow_id: ID of the workflow
        thread_id: ID of the thread
        
    Returns:
        Thread object with full message history
    """
    try:
        from src.persistence.threads import get_thread_repository
        
        repo = get_thread_repository()
        thread = await repo.get(thread_id, workflow_id)
        
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")
        
        logger.info(f"Retrieved workflow thread: {thread_id}")
        
        return {
            "id": thread.id,
            "agent_id": thread.agent_id,
            "title": f"Conversation",
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if hasattr(m, 'timestamp') else datetime.utcnow().isoformat(),
                }
                for m in thread.messages
            ],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workflow thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}/threads/{thread_id}", name="delete_workflow_thread")
async def delete_workflow_thread(
    workflow_id: str = Path(..., description="Workflow ID"),
    thread_id: str = Path(..., description="Thread ID")
):
    """
    Delete a workflow thread.
    
    Args:
        workflow_id: ID of the workflow
        thread_id: ID of the thread
    """
    try:
        from src.persistence.threads import get_thread_repository
        
        repo = get_thread_repository()
        thread = await repo.get(thread_id, workflow_id)
        
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")
        
        await repo.delete(thread_id, workflow_id)
        
        logger.info(f"Deleted workflow thread: {thread_id}")
        
        return {"status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{workflow_id}/threads/{thread_id}", name="update_workflow_thread")
async def update_workflow_thread(
    workflow_id: str = Path(..., description="Workflow ID"),
    thread_id: str = Path(..., description="Thread ID"),
    request: Optional[dict] = Body(None)
):
    """
    Update a workflow thread (title, metadata, etc).
    
    Args:
        workflow_id: ID of the workflow
        thread_id: ID of the thread
        request: Request body with fields to update (e.g., title)
        
    Returns:
        Updated thread object
    """
    try:
        from src.persistence.threads import get_thread_repository
        
        repo = get_thread_repository()
        thread = await repo.get(thread_id, workflow_id)
        
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")
        
        # Update fields from request
        if request:
            if "title" in request:
                thread.title = request["title"]
        
        # Save updated thread
        updated_thread = await repo.update(thread)
        
        logger.info(f"Updated workflow thread: {thread_id}")
        
        return {
            "id": updated_thread.id,
            "agent_id": updated_thread.agent_id,
            "title": updated_thread.title or "Untitled",
            "created_at": updated_thread.created_at.isoformat(),
            "updated_at": updated_thread.updated_at.isoformat(),
            "messages": [],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/threads/{thread_id}/messages", name="add_workflow_thread_message")
async def add_workflow_thread_message(
    workflow_id: str = Path(..., description="Workflow ID"),
    thread_id: str = Path(..., description="Thread ID"),
    request: Optional[ChatRequest] = None
):
    """
    Add a message to a workflow thread.
    
    Args:
        workflow_id: ID of the workflow
        thread_id: ID of the thread
        request: Chat request with message and role
        
    Returns:
        Updated thread object
    """
    if request is None:
        raise HTTPException(status_code=400, detail="Request body required")
    
    try:
        from src.persistence.threads import get_thread_repository
        from src.persistence.models import Message
        
        repo = get_thread_repository()
        thread = await repo.get(thread_id, workflow_id)
        
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")
        
        # Create message
        message = Message(
            id=f"msg_{int(asyncio.get_event_loop().time() * 1000)}",
            role=getattr(request, 'role', 'assistant'),  # Default to 'assistant' if not provided
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        # Add message to thread
        updated_thread = await repo.add_message(thread_id, workflow_id, message, thread)
        
        logger.info(f"Added message to workflow thread: {thread_id}")
        
        return {
            "id": updated_thread.id,
            "agent_id": updated_thread.agent_id,
            "title": f"Conversation",
            "created_at": updated_thread.created_at.isoformat(),
            "updated_at": updated_thread.updated_at.isoformat(),
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat() if hasattr(m, 'timestamp') else datetime.utcnow().isoformat(),
                }
                for m in updated_thread.messages
            ],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message to workflow thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

