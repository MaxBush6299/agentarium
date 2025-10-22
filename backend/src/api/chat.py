"""
Chat API Router
RESTful API endpoints for agent conversations with SSE streaming.
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse

from src.persistence.models import ChatRequest, Thread, ThreadListResponse, Message, RunStatus, StepStatus, ToolCall, Step, StepType, AgentStatus
from src.persistence.threads import get_thread_repository
from src.persistence.runs import get_run_repository
from src.persistence.steps import get_step_repository
from src.persistence.agents import get_agent_repository
from src.api.streaming import EventGenerator
from src.agents.factory import AgentFactory
from src.agents.base import DemoBaseAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["Chat"])


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify routing works"""
    print("\n🔥🔥🔥 TEST ENDPOINT HIT 🔥🔥🔥\n")
    return {"status": "ok", "message": "Chat API is working"}


async def get_agent(agent_id: str) -> Optional[DemoBaseAgent]:
    """
    Get agent by ID from Cosmos DB and create via factory.
    
    This function:
    1. Loads agent metadata from Cosmos DB via AgentRepository
    2. Validates agent is active and public
    3. Creates agent using AgentFactory with graceful tool loading
    4. Handles failures gracefully with logging
    
    Features:
    - Dynamic agent loading from configuration (Cosmos DB)
    - Lazy tool loading with per-tool error handling
    - Graceful degradation: agent works even if tools fail
    - No hardcoded agent classes needed
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        DemoBaseAgent instance if successful, None otherwise
    """
    try:
        # Get agent configuration from Cosmos DB
        logger.info(f"🔍 Attempting to load agent: {agent_id}")
        print(f"[GET_AGENT] Loading agent: {agent_id}")
        logger.info(f"[DEBUG] Requesting agent repository...")
        repo = get_agent_repository()
        logger.info(f"[DEBUG] Repository instance: {repo}")
        logger.debug(f"Repository initialized, fetching agent from Cosmos DB")
        
        logger.info(f"[DEBUG] Calling repo.get('{agent_id}')...")
        print(f"[GET_AGENT] Calling repo.get('{agent_id}')...")
        agent_config = repo.get(agent_id)
        print(f"[GET_AGENT] repo.get() returned: {agent_config}")
        logger.info(f"[DEBUG] repo.get() returned: {agent_config}")
        
        if not agent_config:
            logger.warning(f"❌ Agent not found in repository: {agent_id}")
            print(f"[GET_AGENT] Agent not found in repository: {agent_id}")
            logger.info(f"Attempting to list all agents to debug...")
            try:
                all_agents = repo.list()
                logger.info(f"[DEBUG] Available agents from list(): {[(a.id, a.status) for a in all_agents]}")
            except Exception as list_err:
                logger.error(f"Failed to list agents: {list_err}")
            return None
        
        # Check if agent is active
        if agent_config.status != AgentStatus.ACTIVE:
            logger.warning(f"⏸️  Agent {agent_id} is not active (status: {agent_config.status})")
            print(f"[GET_AGENT] Agent not active: {agent_id} (status: {agent_config.status})")
            return None
        
        # Create agent from metadata using factory
        # This includes lazy tool loading with graceful failure per tool
        print(f"[GET_AGENT] Creating agent from metadata with {len(agent_config.tools)} tools")
        logger.info(f"Creating agent from metadata with {len(agent_config.tools)} tools")
        agent = AgentFactory.create_from_metadata(agent_config)
        
        if not agent:
            logger.error(f"❌ Failed to create agent from metadata: {agent_id}")
            print(f"[GET_AGENT] Failed to create agent from metadata: {agent_id}")
            return None
        
        print(f"[GET_AGENT] ✅ Successfully created agent '{agent_id}'")
        logger.info(f"✅ Successfully created agent '{agent_id}' from Cosmos DB metadata")
        return agent
        
    except Exception as e:
        logger.error(f"❌ Error getting agent {agent_id}: {type(e).__name__}: {e}", exc_info=True)
        return None


@router.post("/{agent_id}/chat")
async def chat_with_agent(
    request: ChatRequest,
    agent_id: str = Path(..., description="Agent ID")
):
    """
    Chat with an agent. Supports SSE streaming for real-time responses.
    
    Args:
        agent_id: Agent ID (e.g., 'support-triage', 'ops-assistant')
        request: Chat request with message and optional thread_id
        
    Returns:
        StreamingResponse with SSE events or JSON response
    """
    logger.info(f"Chat request for agent {agent_id}: {request.message[:50]}...")
    
    try:
        # Get agent from Cosmos DB and create via factory
        agent = await get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Get or create thread
        thread_repo = get_thread_repository()
        
        if request.thread_id:
            thread = await thread_repo.get(request.thread_id, agent_id)
            if not thread:
                raise HTTPException(status_code=404, detail=f"Thread {request.thread_id} not found")
            if thread.agent_id != agent_id:
                raise HTTPException(status_code=400, detail="Thread belongs to different agent")
        else:
            # Create new thread
            thread = await thread_repo.create(agent_id=agent_id)
            logger.info(f"Created new thread {thread.id}")
        
        # Add user message to thread
        user_message_id = f"msg_{uuid.uuid4().hex[:12]}"
        user_message = Message(
            id=user_message_id,
            role="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        thread = await thread_repo.add_message(thread.id, agent_id, user_message, thread=thread)
        logger.info(f"Added user message {user_message_id} to thread {thread.id}")
        
        # Create run
        run_repo = get_run_repository()
        run = await run_repo.create(
            thread_id=thread.id,
            agent_id=agent_id,
            user_message_id=user_message_id,
            model="gpt-4o",  # Default model, can be made configurable later
            temperature=0.7
        )
        logger.info(f"Created run {run.id}")
        
        # Add run to thread
        await thread_repo.add_run(thread.id, agent_id, run.id, thread=thread)
        
        # Start streaming response
        if request.stream:
            return StreamingResponse(
                stream_chat_response(agent, thread, run, request.message),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                    "Connection": "keep-alive",
                }
            )
        else:
            # Non-streaming response (synchronous)
            # TODO: Implement non-streaming mode if needed
            raise HTTPException(status_code=501, detail="Non-streaming mode not yet implemented")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def stream_chat_response(agent, thread: Thread, run, user_message: str):
    """
    Stream chat response with SSE events.
    
    Args:
        agent: Agent instance (SupportTriageAgent or AzureOpsAgent)
        thread: Thread object from Cosmos DB
        run: Run object from Cosmos DB
        user_message: User message content
        
    Yields:
        SSE-formatted event strings
    """
    print("\n========== STREAM START ==========")
    print(f"[stream_chat_response] Entered function for run {run.id}")
    
    event_gen = EventGenerator(heartbeat_interval=15.0)
    run_repo = get_run_repository()
    thread_repo = get_thread_repository()
    step_repo = get_step_repository()
    
    error_occurred = False
    error_message = None
    
    try:
        print("[1] Updating run status to IN_PROGRESS")
        # Update run status to in_progress
        await run_repo.update_status(run.id, thread.id, RunStatus.IN_PROGRESS, run=run)
        print("[2] Run status updated")
        
        # Collect assistant response
        assistant_response = ""
        assistant_message_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        # Get or create agent framework thread
        print("[3] Getting new agent thread")
        agent_thread = agent.get_new_thread()
        print(f"[4] Agent thread created: {agent_thread}")
        print(f"[4a] Agent object: {agent}")
        print(f"[4b] Agent.agent object: {agent.agent}")
        
        print(f"[5] Starting agent stream for message: {user_message[:50]}...")
        
        # Debug agent methods
        print("[5.1] Inspecting agent methods:")
        print(f"[5.1a] hasattr(agent, 'run'): {hasattr(agent, 'run')}")
        print(f"[5.1b] hasattr(agent, 'run_stream'): {hasattr(agent, 'run_stream')}")
        print(f"[5.1c] hasattr(agent, 'agent'): {hasattr(agent, 'agent')}")
        print(f"[5.1d] hasattr(agent.agent, 'run'): {hasattr(agent.agent, 'run')}")
        print(f"[5.1e] hasattr(agent.agent, 'run_stream'): {hasattr(agent.agent, 'run_stream')}")
        
        # Check run method signature
        import inspect
        if hasattr(agent, 'run'):
            run_sig = inspect.signature(agent.run)
            print(f"[5.1f] agent.run signature: {run_sig}")
            print(f"[5.1g] agent.run is coroutine? {inspect.iscoroutinefunction(agent.run)}")
        
        if hasattr(agent.agent, 'run'):
            agent_run_sig = inspect.signature(agent.agent.run)
            print(f"[5.1h] agent.agent.run signature: {agent_run_sig}")
            print(f"[5.1i] agent.agent.run is coroutine? {inspect.iscoroutinefunction(agent.agent.run)}")
        
        # Try calling agent.run() first (non-streaming) to see if that works
        print("[6] Attempting to call agent.run() (non-streaming first)")
        try:
            print("[6.0] Setting up run call with timeout...")
            
            from src.config import settings
            print(f"[6.0-DEBUG] Agent info:")
            print(f"  - Model: {agent.model}")
            print(f"  - Name: {agent.name}")
            print(f"  - ENDPOINT: {settings.AZURE_OPENAI_ENDPOINT}")
            sys.stdout.flush()
            
            # Try non-streaming first with a timeout
            import asyncio
            print("[6.1] About to call agent.run() with 30 second timeout...")
            sys.stdout.flush()
            
            try:
                run_response = await asyncio.wait_for(
                    agent.run(user_message, thread=agent_thread),
                    timeout=30.0
                )
                print(f"[6.2] ✓ Got run_response: {type(run_response).__name__}")
                print(f"[6.2a] Response has messages: {hasattr(run_response, 'messages')}")
                print(f"[6.2b] Response has text: {hasattr(run_response, 'text')}")
                
                # Check for tool calls in the response
                if hasattr(run_response, 'messages') and run_response.messages:
                    print(f"[6.2-TRACE] Response has {len(run_response.messages)} messages")
                    sys.stdout.flush()
                    tool_call_index = 0
                    
                    for i, msg in enumerate(run_response.messages):
                        msg_role = getattr(msg, 'role', None)
                        
                        # Convert Role enum to string if needed
                        if hasattr(msg_role, 'value'):
                            role_str = str(msg_role.value)  # type: ignore
                        else:
                            role_str = str(msg_role)
                        
                        print(f"[6.2-TRACE-{i}a] Message role: {role_str}")
                        
                        # Show all message attributes
                        msg_vars = vars(msg)
                        msg_attrs = {k: type(v).__name__ for k, v in msg_vars.items()}
                        print(f"[6.2-TRACE-{i}b] Message attributes: {msg_attrs}")
                        
                        # Show author_name if present
                        if 'author_name' in msg_vars:
                            print(f"[6.2-TRACE-{i}c] Author: {msg_vars['author_name']}")
                        sys.stdout.flush()
                        
                        # Check if this is a tool call message
                        if role_str == 'tool':
                            print(f"[6.2-TRACE-{i}] *** TOOL CALL DETECTED ***")
                            sys.stdout.flush()
                            tool_call_index += 1
                            step_id = f"tool_{tool_call_index}"
                            
                            # Look back at previous assistant message for the tool call request
                            tool_call_request = None
                            if i > 0:
                                prev_msg = run_response.messages[i - 1]
                                prev_role = getattr(prev_msg, 'role', None)
                                prev_role_str = None
                                if prev_role is not None:
                                    if hasattr(prev_role, 'value'):
                                        prev_role_str = str(prev_role.value)  # type: ignore
                                    else:
                                        prev_role_str = str(prev_role)
                                
                                if prev_role_str == 'assistant':
                                    prev_vars = vars(prev_msg)
                                    if 'contents' in prev_vars:
                                        # Assistant message might have ToolUseBlock or similar
                                        print(f"[6.2-TRACE-{i}d] Previous assistant message has {len(prev_vars['contents'])} content items")
                                        for content_item in prev_vars['contents']:
                                            content_vars = vars(content_item)
                                            print(f"[6.2-TRACE-{i}e] Content type: {type(content_item).__name__}")
                                            print(f"[6.2-TRACE-{i}f] Content attrs: {list(content_vars.keys())}")
                                            # Try to extract tool use info
                                            tool_call_request = {}
                                            if 'id' in content_vars and content_vars['id']:
                                                tool_call_request['id'] = content_vars['id']
                                            if 'name' in content_vars and content_vars['name']:
                                                tool_call_request['name'] = content_vars['name']
                                            if 'arguments' in content_vars and content_vars['arguments']:
                                                # arguments contains the input parameters
                                                tool_call_request['arguments'] = content_vars['arguments']
                                            if 'input' in content_vars and content_vars['input']:
                                                tool_call_request['input'] = content_vars['input']
                            
                            if tool_call_request:
                                print(f"[6.2-TRACE-{i}g] Tool call request found: {json.dumps({k: str(v)[:100] if v else None for k, v in tool_call_request.items()}, indent=2)}")
                            sys.stdout.flush()
                            
                            # Extract tool call details from contents array
                            tool_name = 'unknown_tool'
                            tool_input = {}
                            call_id = None
                            
                            # Add request details if available
                            if tool_call_request:
                                tool_input['request'] = tool_call_request
                                if 'name' in tool_call_request:
                                    tool_name = tool_call_request['name']
                            
                            try:
                                msg_vars = vars(msg)
                                if 'contents' in msg_vars and msg_vars['contents']:
                                    for idx, content_item in enumerate(msg_vars['contents']):
                                        content_vars = vars(content_item)
                                        
                                        # Extract call_id (identifies which tool was called)
                                        if 'call_id' in content_vars:
                                            call_id = content_vars['call_id']
                                            if tool_name == 'unknown_tool':
                                                tool_name = str(call_id)
                                            tool_input['call_id'] = call_id
                                        
                                        # Extract result - it's a list of TextContent objects
                                        if 'result' in content_vars and isinstance(content_vars['result'], list):
                                            result_texts = []
                                            for result_item in content_vars['result']:
                                                result_vars = vars(result_item)
                                                # TextContent has a 'text' attribute
                                                if 'text' in result_vars:
                                                    result_texts.append(result_vars['text'])
                                            if result_texts:
                                                tool_input['result'] = '\n'.join(result_texts)
                                        
                                        # Include type and exception if present
                                        if 'type' in content_vars:
                                            tool_input['type'] = content_vars['type']
                                        if 'exception' in content_vars and content_vars['exception']:
                                            tool_input['exception'] = str(content_vars['exception'])
                            except Exception as e:
                                print(f"[DEBUG-TOOL] Error extracting: {e}")
                                import traceback
                                traceback.print_exc()
                            sys.stdout.flush()
                            
                            print(f"[6.2-TRACE-{i}c] Sending trace_start for tool call")
                            sys.stdout.flush()
                            
                            try:
                                await event_gen.send_trace_start(
                                    step_id=step_id,
                                    tool_name=tool_name,
                                    tool_type='agent_tool',
                                    input_data=tool_input if isinstance(tool_input, dict) else {'args': str(tool_input)}
                                )
                                print(f"[6.2-TRACE-{i}c] ✓ trace_start sent")
                            except Exception as e:
                                print(f"[6.2-TRACE-{i}c] ✗ ERROR: {e}")
                                import traceback
                                traceback.print_exc()
                            sys.stdout.flush()
                
                # Extract the response text
                if hasattr(run_response, 'text') and run_response.text:
                    assistant_response = run_response.text
                    print(f"[6.2c] Got response text: {len(assistant_response)} chars")
                    print(f"[6.2d] First 100 chars: {assistant_response[:100]}")
                    
                    # Stream it in chunks
                    print("[6.3] Streaming response in chunks...")
                    chunk_size = 50
                    for i in range(0, len(assistant_response), chunk_size):
                        chunk = assistant_response[i:i+chunk_size]
                        await event_gen.send_token(chunk)
                        sys.stdout.flush()
                    print(f"[6.4] Finished streaming {len(assistant_response)} chars")
                elif hasattr(run_response, 'messages') and run_response.messages:
                    # Try to extract text from messages
                    for msg in run_response.messages:
                        if hasattr(msg, 'content'):
                            assistant_response += msg.content
                    print(f"[6.2c-ALT] Extracted text from messages: {len(assistant_response)} chars")
                    
                    # Stream it
                    chunk_size = 50
                    for i in range(0, len(assistant_response), chunk_size):
                        chunk = assistant_response[i:i+chunk_size]
                        await event_gen.send_token(chunk)
                else:
                    print(f"[6.2-ERROR] Could not extract text from response!")
                    print(f"[6.2-ERROR-DUMP] Response: {run_response}")
                    assistant_response = "Agent responded but response format was unexpected"
                    await event_gen.send_token(assistant_response)
                    
            except asyncio.TimeoutError:
                print(f"[6.1-TIMEOUT] agent.run() timed out after 30 seconds!")
                print(f"[6.1-TIMEOUT] This indicates the Azure OpenAI SDK is blocking on network I/O")
                raise
                
        except Exception as run_error:
            print(f"\n[6.ERROR] !!!!!! CAUGHT EXCEPTION IN RUN BLOCK !!!!!")
            print(f"[6.ERROR.1] Error type: {type(run_error).__name__}")
            print(f"[6.ERROR.2] Error message: {run_error}")
            import traceback
            print(f"[6.ERROR.3] Full traceback:")
            traceback.print_exc()
            raise
        
        print(f"[7] Run completed")
        print(f"[8] Assistant response collected ({len(assistant_response)} chars)")
        
        # Add assistant message to thread
        print("[10] Adding assistant message to thread")
        assistant_message = Message(
            id=assistant_message_id,
            role="assistant",
            content=assistant_response,
            timestamp=datetime.utcnow()
        )
        await thread_repo.add_message(thread.id, thread.agent_id, assistant_message, thread=thread)
        print("[11] Assistant message added")
        
        # Update run with assistant message ID
        print("[12] Setting assistant message ID on run")
        await run_repo.set_assistant_message(run.id, thread.id, assistant_message_id, run=run)
        print("[13] Assistant message ID set")
        
        # Update run status to completed
        print("[14] Calculating tokens and updating status")
        tokens_used = len(user_message.split()) * 2 + len(assistant_response.split()) * 2
        await run_repo.update_tokens(run.id, thread.id, tokens_used // 2, tokens_used // 2, cost_usd=0, run=run)
        await run_repo.update_status(run.id, thread.id, RunStatus.COMPLETED, run=run)
        print("[15] Status updated to COMPLETED")
        
        # Send done event
        print("[16] Sending done event")
        await event_gen.send_done(
            run_id=run.id,
            thread_id=thread.id,
            message_id=assistant_message_id,
            tokens_used=tokens_used
        )
        print("[17] Done event sent")
    
    except Exception as e:
        logging.error(f"Error generating response: {type(e).__name__}: {str(e)}")
        
        error_occurred = True
        error_message = str(e)
        
        # Try to update run status to failed
        try:
            await run_repo.update_status(run.id, thread.id, RunStatus.FAILED, error=error_message, run=run)
        except Exception as update_error:
            logging.error(f"Could not update run status: {update_error}")
        
        # Queue error event
        await event_gen.send_error(error=error_message, details="Error generating response")
    
    finally:
        event_count = 0
        try:
            # Stream all queued events
            async for event_str in event_gen.stream():
                event_count += 1
                try:
                    yield event_str
                except Exception as yield_error:
                    logging.error(f"Error yielding event: {yield_error}")
                    break
        except Exception as stream_loop_error:
            logging.error(f"Error in event stream loop: {stream_loop_error}")
        finally:
            print("[F5] Closing event generator")
            try:
                await event_gen.close()
                print("[F6] Event generator closed successfully")
            except Exception as close_error:
                print(f"[F7] Error closing event generator: {close_error}")
        
        print("========== FINALLY BLOCK END ==========\n")


@router.post("/{agent_id}/threads")
async def create_thread(
    agent_id: str = Path(..., description="Agent ID")
):
    """
    Create a new thread for an agent.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Created Thread object
    """
    try:
        thread_repo = get_thread_repository()
        
        thread = await thread_repo.create(agent_id)
        
        return thread
    
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/threads")
async def list_threads(
    agent_id: str = Path(..., description="Agent ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum threads to return"),
    offset: int = Query(0, ge=0, description="Number of threads to skip"),
    status: str = Query("active", description="Thread status filter")
):
    """
    List threads for an agent.
    
    Args:
        agent_id: Agent ID
        limit: Maximum threads to return
        offset: Number of threads to skip
        status: Thread status filter
        
    Returns:
        List of threads with pagination info
    """
    try:
        thread_repo = get_thread_repository()
        
        threads = await thread_repo.list(
            agent_id=agent_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        total = await thread_repo.count(agent_id=agent_id, status=status)
        
        return ThreadListResponse(
            threads=threads,
            total=total,
            page=(offset // limit) + 1,
            page_size=limit
        )
    
    except Exception as e:
        logger.error(f"Error listing threads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/threads/{thread_id}")
async def get_thread(
    agent_id: str = Path(..., description="Agent ID"),
    thread_id: str = Path(..., description="Thread ID")
):
    """
    Get a specific thread with full message history.
    
    Args:
        agent_id: Agent ID
        thread_id: Thread ID
        
    Returns:
        Thread object with messages
    """
    try:
        thread_repo = get_thread_repository()
        
        thread = await thread_repo.get(thread_id, agent_id)
        
        if not thread:
            raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
        
        if thread.agent_id != agent_id:
            raise HTTPException(status_code=400, detail="Thread belongs to different agent")
        
        return thread
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/threads/{thread_id}")
async def delete_thread(
    agent_id: str = Path(..., description="Agent ID"),
    thread_id: str = Path(..., description="Thread ID"),
    hard_delete: bool = Query(False, description="Permanently delete (true) or soft delete (false)")
):
    """
    Delete a thread.
    
    Args:
        agent_id: Agent ID
        thread_id: Thread ID
        hard_delete: If True, permanently delete; if False, mark as deleted
        
    Returns:
        Success message
    """
    try:
        thread_repo = get_thread_repository()
        
        # Verify thread belongs to agent (if it exists)
        thread = await thread_repo.get(thread_id, agent_id)
        if thread and thread.agent_id != agent_id:
            raise HTTPException(status_code=400, detail="Thread belongs to different agent")
        
        # Delete thread (idempotent - succeeds even if thread doesn't exist)
        await thread_repo.delete(thread_id, agent_id, soft_delete=not hard_delete)
        
        delete_type = "permanently deleted" if hard_delete else "soft deleted"
        return {"message": f"Thread {thread_id} {delete_type}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
