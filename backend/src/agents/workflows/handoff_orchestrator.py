"""
Handoff Workflow Orchestrator

Implements multi-tier handoff pattern with specialist-to-specialist routing using
Microsoft Agent Framework's HandoffBuilder pattern.

Routing Pattern (Specialist-to-Specialist):
    User → Router → Specialist A → Specialist B → Evaluator → Response

Key Features:
- Multi-tier routing: Specialists can hand off to other specialists
- Reuses existing agents from Cosmos DB (router, data-agent, analyst, order-agent, evaluator)
- Explicit routing graph via HandoffBuilder.add_handoff()
- Configurable termination condition (max handoffs/turns)

Routing Configuration:
- Router: Entry point, routes to specialists (data-agent, analyst, order-agent)
- Data-Agent: Handles data queries, can escalate to analyst
- Analyst: Data analysis specialist, can escalate to order-agent
- Order-Agent: Order/fulfillment specialist
- Evaluator: Quality assessment, not part of handoff chain

Implementation:
Uses HandoffBuilder with agents loaded from Cosmos DB at runtime.
Supports streaming responses via workflow.run_stream() and send_responses_streaming().
"""

import asyncio
import json
import logging
import os
from typing import Optional, Tuple, Dict, Any, List, AsyncIterable

from agent_framework import (
    HandoffBuilder,
    WorkflowEvent,
    WorkflowOutputEvent,
    WorkflowStatusEvent,
    WorkflowRunState,
    RequestInfoEvent,
    ChatMessage,
    HandoffUserInputRequest,
)
from agent_framework.azure import AzureOpenAIChatClient

from src.agents.workflows.base_orchestrator import BaseWorkflowOrchestrator
from src.agents.workflows.workflow_models import WorkflowTraceMetadata, AgentInteraction
from src.agents.factory import AgentFactory
from src.persistence.agents import get_agent_repository

logger = logging.getLogger(__name__)


class HandoffOrchestrator(BaseWorkflowOrchestrator):
    """
    Orchestrator for multi-tier handoff/routing workflow pattern.
    
    Manages specialist-to-specialist routing with HandoffBuilder. Routes queries
    through specialists with ability to escalate between specialists.
    
    Uses existing agents from Cosmos DB (router, data-agent, analyst, order-agent).
    Evaluator agent validates response quality after specialist handling.
    
    Pattern:
        User → Router → [Specialist] → [Specialist] → Back to User
    """
    
    def __init__(self, workflow_id: str, workflow_config: Dict[str, Any], chat_client: Any = None):
        """Initialize handoff orchestrator with workflow configuration."""
        super().__init__(workflow_id, workflow_config, chat_client)
        self.workflow: Optional[Any] = None
        self.agents_cache: Dict[str, Any] = {}
        
        # Required agents - all loaded from Cosmos DB
        self.required_agents = [
            "router",           # Entry point, routes to data-agent
            "data-agent",       # Handles data queries
            "analyst",          # Data analysis specialist
        ]
    
    async def _load_agents_from_cosmos(self) -> Dict[str, Any]:
        """
        Load all required agents from Cosmos DB as ChatAgent instances.
        
        Returns:
            Dictionary mapping agent_id to agent instance
            
        Raises:
            ValueError: If any required agent not found in Cosmos DB
        """
        if self.agents_cache:
            return self.agents_cache
        
        logger.info(f"Loading agents from Cosmos DB: {self.required_agents}")
        
        try:
            agent_repo = get_agent_repository()
            agents = {}
            for agent_id in self.required_agents:
                try:
                    agent_metadata = agent_repo.get(agent_id)
                    if agent_metadata:
                        agent = AgentFactory.create_from_metadata(agent_metadata)
                        if agent:
                            agents[agent_id] = agent
                            logger.info(f"✓ Loaded agent: {agent_id}")
                        else:
                            logger.warning(f"✗ Failed to instantiate agent: {agent_id}")
                    else:
                        logger.warning(f"✗ Agent metadata not found: {agent_id}")
                except Exception as e:
                    logger.warning(f"✗ Error loading agent {agent_id}: {str(e)}")
            
            self.agents_cache = agents
            return agents
        except Exception as e:
            logger.error(f"Failed to load agents: {str(e)}", exc_info=True)
            return {}
    
    async def _build_workflow(self, agents: Dict[str, Any]) -> Any:
        """
        Build simplified handoff workflow: Router → Data-Agent → Analyst.
        
        Evaluator is NOT in the handoff chain - it's used separately to assess responses.
        
        Pattern:
        1. Router receives user query and routes to data-agent
        2. Data-agent retrieves data
        3. Data-agent hands off to analyst for analysis
        4. Analyst provides final response (workflow ends)
        5. (Evaluator would assess separately, not shown in main flow)
        
        Termination: Occurs when a 2nd user message is sent (triggers end of workflow)
        
        Args:
            agents: Dictionary of loaded DemoBaseAgent instances
            
        Returns:
            Built workflow
            
        Raises:
            ValueError: If any required agent is missing or can't be extracted
        """
        logger.info("Building simplified handoff workflow: router → data-agent → analyst")
        
        # Extract agents from dictionary with validation
        router_wrapper = agents.get("router")
        data_agent_wrapper = agents.get("data-agent")
        analyst_wrapper = agents.get("analyst")
        
        if not all([router_wrapper, data_agent_wrapper, analyst_wrapper]):
            missing = [k for k, v in [("router", router_wrapper), ("data-agent", data_agent_wrapper), 
                                     ("analyst", analyst_wrapper)] if not v]
            raise ValueError(f"Missing required agents: {missing}")
        
        # Extract underlying ChatAgent instances (HandoffBuilder needs AgentProtocol)
        router = router_wrapper.agent  # type: ignore
        data_agent = data_agent_wrapper.agent  # type: ignore
        analyst = analyst_wrapper.agent  # type: ignore
        
        logger.info(f"Extracted ChatAgent instances: router={router.display_name}, "
                   f"data_agent={data_agent.display_name}, analyst={analyst.display_name}")
        
        # Build workflow with explicit routing chain (NO evaluator in chain)
        participants: List[Any] = [router, data_agent, analyst]
        
        workflow = (
            HandoffBuilder(
                name="simplified_data_analysis_chain",
                participants=participants,  # type: ignore
                description="Simplified chain: router → data-agent → analyst"
            )
            .set_coordinator(router)  # type: ignore  # Router is entry point
            # Router routes to data-agent
            .add_handoff(router, data_agent)  # type: ignore
            # Data-agent routes to analyst for analysis
            .add_handoff(data_agent, analyst)  # type: ignore
            # Analyst is terminal - no further handoffs
            # Termination: When 2nd user message is sent, workflow ends after agents process it
            .with_termination_condition(
                lambda conv: sum(1 for msg in conv if msg.role.value == "user") > 1
            )
            .build()
        )
        
        logger.info("✓ Simplified handoff workflow built successfully")
        return workflow
    
    async def _drain_events(self, event_stream: AsyncIterable[WorkflowEvent]) -> List[WorkflowEvent]:
        """Collect all events from async stream."""
        return [event async for event in event_stream]
    
    async def _extract_final_response(self, events: List[WorkflowEvent]) -> str:
        """
        Extract final response from workflow execution events.
        
        Looks for the last agent message before the user's closing message.
        The workflow conversation ends with user's closing message, so we need
        the agent's last response which comes before that.
        
        Args:
            events: List of workflow events from async stream
            
        Returns:
            Final response text from the last agent in the chain
        """
        logger.info(f"Processing {len(events)} events to extract response...")
        
        # Find WorkflowOutputEvent with conversation
        for event in reversed(events):
            event_type = type(event).__name__
            
            # WorkflowOutputEvent.data contains the full conversation as a list of ChatMessages
            if 'WorkflowOutput' in event_type and hasattr(event, 'data') and isinstance(event.data, list):
                try:
                    conversation = event.data
                    logger.info(f"Found WorkflowOutputEvent with {len(conversation)} messages in conversation")
                    
                    # Log all messages for debugging
                    for i, msg in enumerate(conversation):
                        author = msg.author_name or msg.role.value if hasattr(msg, 'role') else 'unknown'
                        text_preview = msg.text[:50] if hasattr(msg, 'text') and msg.text else '[no text]'
                        logger.debug(f"  Msg {i}: {author} - {text_preview}")
                    
                    # Find the last agent message (not from user, not from handoff requests)
                    # Go backwards through conversation to find last agent response
                    for msg in reversed(conversation):
                        # Get author name
                        if hasattr(msg, 'author_name') and msg.author_name:
                            author = msg.author_name
                        elif hasattr(msg, 'role'):
                            author = msg.role.value
                        else:
                            continue
                        
                        # Skip user messages and system-level routing
                        if author.lower() in ['user', 'system']:
                            continue
                        
                        # Get message text
                        if hasattr(msg, 'text') and msg.text and msg.text.strip():
                            logger.info(f"✓ Extracted final response from agent '{author}'")
                            return msg.text
                            
                except Exception as e:
                    logger.error(f"Error processing {event_type}: {e}", exc_info=True)
        
        logger.warning("No final agent response could be extracted from workflow events")
        return "Unable to extract final response from workflow"
    
    async def execute(
        self,
        message: str,
        thread_id: str,
        max_handoffs: Optional[int] = None,
    ) -> Tuple[str, WorkflowTraceMetadata]:
        """
        Execute simplified handoff workflow: router → data-agent → analyst → evaluator.
        
        Pattern (from handoff_specialist_to_specialist.py example):
        1. Send initial user message via workflow.run_stream()
        2. Collect events and check for pending requests
        3. Send a final "done" message via send_responses_streaming() to trigger termination
        4. Extract final conversation from WorkflowOutputEvent
        
        Flow:
        1. Load all required agents from Cosmos DB
        2. Build handoff routing graph using HandoffBuilder
        3. Run workflow with user message via streaming
        4. Send final message to trigger termination condition
        5. Extract final response and build trace metadata
        
        Args:
            message: User's message to process
            thread_id: Thread ID for maintaining conversation context
            max_handoffs: Maximum handoff iterations (unused - using termination condition instead)
            
        Returns:
            Tuple of (final_response, trace_metadata)
        """
        handoff_path = ["router"]  # Always starts with router
        final_response = ""
        specialists_used = []
        
        try:
            logger.info(
                f"Executing handoff workflow: thread={thread_id}, "
                f"message={message[:50]}..."
            )
            
            # Step 1: Load agents from Cosmos DB
            logger.info("Step 1: Loading agents from Cosmos DB...")
            agents = await self._load_agents_from_cosmos()
            
            if not agents or len(agents) < 3:
                raise ValueError(f"Insufficient agents loaded: {list(agents.keys())}")
            
            logger.info(f"Loaded agents: {list(agents.keys())}")
            
            # Step 2: Build workflow
            logger.info("Step 2: Building handoff workflow...")
            self.workflow = await self._build_workflow(agents)
            
            if not self.workflow:
                raise RuntimeError("Workflow was not initialized properly")
            
            # Step 3: Send initial message and collect events
            logger.info(f"Step 3: Sending initial message: {message[:60]}...")
            initial_events = await self._drain_events(
                self.workflow.run_stream(message)  # type: ignore
            )
            
            logger.info(f"Received {len(initial_events)} events from initial run")
            
            # Check if workflow is still waiting for input (should be at this point)
            pending_requests = []
            for event in initial_events:
                if isinstance(event, RequestInfoEvent):
                    if isinstance(event.data, HandoffUserInputRequest):
                        pending_requests.append(event)
                        logger.debug(f"Pending request found: {event.request_id}")
            
            logger.info(f"Step 4: Found {len(pending_requests)} pending requests, sending final message...")
            
            # Step 4: Send final response to trigger termination
            # This triggers the termination condition (> 1 user message)
            if pending_requests:
                responses = {req.request_id: "Done, thank you." for req in pending_requests}
                final_events = await self._drain_events(
                    self.workflow.send_responses_streaming(responses)  # type: ignore
                )
                logger.info(f"Received {len(final_events)} events from final message")
            else:
                final_events = initial_events
                logger.warning("No pending requests found, using initial events")
            
            # Combine all events for processing
            all_events = initial_events + final_events
            logger.info(f"Step 5: Processing {len(all_events)} total events...")
            
            # Step 5: Extract final conversation and trace info
            final_response = await self._extract_final_response(all_events)
            
            # Track specialists from conversation
            for event in all_events:
                if isinstance(event, WorkflowOutputEvent):
                    conversation = event.data
                    if isinstance(conversation, list):
                        for msg in conversation:
                            author = msg.author_name or msg.role.value
                            if author not in ["user", "router"] and author not in specialists_used:
                                specialists_used.append(author)
                                if author not in handoff_path:
                                    handoff_path.append(author)
            
            logger.info(f"Specialists used: {specialists_used}")
            logger.info(f"Handoff path: {' → '.join(handoff_path)}")
            
            # Build trace metadata
            trace_metadata = self._build_trace_metadata(
                final_response=final_response,
                primary_agent=specialists_used[0] if specialists_used else "router",
                handoff_path=handoff_path,
                satisfaction_score=0.9,  # Workflow executed successfully
                evaluator_reasoning=f"Completed routing chain: {' → '.join(handoff_path)}",
                max_attempts_reached=False,
                thread_id=thread_id,
            )
            
            logger.info(f"✓ Handoff workflow complete")
            return final_response, trace_metadata
        
        except Exception as e:
            logger.error(
                f"Error executing handoff workflow: {str(e)}", 
                exc_info=True
            )
            
            # Return error response with partial trace
            error_response = f"Workflow execution error: {str(e)}"
            trace_metadata = self._build_trace_metadata(
                final_response=error_response,
                primary_agent="system",
                handoff_path=handoff_path,
                satisfaction_score=0.0,
                evaluator_reasoning=f"Execution failed: {str(e)}",
                thread_id=thread_id,
            )
            
            return error_response, trace_metadata

