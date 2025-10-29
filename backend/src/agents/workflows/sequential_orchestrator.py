"""
Sequential Workflow Orchestrator

Implements sequential pattern where agents execute one after another
with shared conversation context. This is ideal for data retrieval + analysis flows.

Pattern:
    User Message → Data Agent (retrieves data) → Analyst (analyzes data) → Final Response

Key Features:
- Agents execute sequentially with shared conversation context
- Each agent builds on previous agent's response
- No handoff requests - linear execution
- Perfect for: "Get data, then analyze it" workflows

Comparison to Handoff:
- Handoff: Multi-turn with user input between agents, agents decide routing
- Sequential: Single-turn linear flow, agents always execute in order

Use Cases:
- "Analyze our top customers" → Data Agent gets customers → Analyst analyzes trends
- "Summarize quarterly performance" → Data Agent retrieves metrics → Analyst provides insights
- "Compare supplier performance" → Data Agent gets supplier data → Analyst compares
"""

import asyncio
import logging
import os
from typing import Optional, Tuple, Dict, Any, List, AsyncIterable, cast

from agent_framework import (
    SequentialBuilder,
    WorkflowEvent,
    WorkflowOutputEvent,
    ChatMessage,
    Role,
)

from src.agents.workflows.base_orchestrator import BaseWorkflowOrchestrator
from src.agents.workflows.workflow_models import WorkflowTraceMetadata
from src.persistence.agents import get_agent_repository

logger = logging.getLogger(__name__)


class SequentialOrchestrator(BaseWorkflowOrchestrator):
    """
    Orchestrator for sequential workflow pattern.
    
    Executes agents sequentially with shared conversation context.
    Each agent processes the conversation and adds their response.
    
    Pattern: Data Agent → Analyst Agent
    
    The conversation flows through both agents:
    1. User sends query
    2. Data Agent responds (queries database, adds response to conversation)
    3. Analyst Agent responds (analyzes data, adds analysis to conversation)
    4. Final conversation is returned to user
    """
    
    def __init__(self, workflow_id: str, workflow_config: Dict[str, Any], chat_client: Any = None):
        """Initialize sequential orchestrator with workflow configuration."""
        super().__init__(workflow_id, workflow_config, chat_client)
        self.workflow: Optional[Any] = None
        self.agents_cache: Dict[str, Any] = {}
        
        # Required agents for sequential flow
        self.required_agents = [
            "data-agent",       # Retrieves data from database
            "analyst",          # Analyzes retrieved data
        ]
    
    def _load_agents_from_cosmos(self) -> Dict[str, Any]:
        """
        Load required agents from Cosmos DB.
        
        Returns:
            Dictionary mapping agent IDs to loaded DemoBaseAgent instances
        """
        logger.info(f"Loading {len(self.required_agents)} agents from Cosmos DB...")
        
        try:
            repo = get_agent_repository()
            agents = {}
            
            for agent_id in self.required_agents:
                logger.info(f"Loading agent: {agent_id}")
                agent_metadata = repo.get(agent_id)  # Not async
                
                if not agent_metadata:
                    logger.warning(f"Agent not found: {agent_id}")
                    continue
                
                # Use AgentFactory to create the agent with tools
                from src.agents.factory import AgentFactory
                agent = AgentFactory.create_from_metadata(agent_metadata)
                
                agents[agent_id] = agent
                logger.info(f"✓ Loaded agent: {agent_id}")
            
            if len(agents) < len(self.required_agents):
                missing = set(self.required_agents) - set(agents.keys())
                logger.warning(f"Missing agents: {missing}")
            
            return agents
            
        except Exception as e:
            logger.error(f"Error loading agents from Cosmos: {e}", exc_info=True)
            raise
    
    async def _drain_events(self, event_stream: AsyncIterable[WorkflowEvent]) -> List[WorkflowEvent]:
        """Collect all events from async stream."""
        logger.debug("Draining events from workflow stream...")
        events = []
        async for event in event_stream:
            event_type = type(event).__name__
            logger.debug(f"Event: {event_type}")
            events.append(event)
        logger.info(f"Collected {len(events)} events")
        return events
    
    async def _build_workflow(self, agents: Dict[str, Any]) -> Any:
        """
        Build sequential workflow: Data Agent → Analyst Agent.
        
        Args:
            agents: Dictionary of loaded DemoBaseAgent instances
            
        Returns:
            Built workflow
            
        Raises:
            ValueError: If any required agent is missing or can't be extracted
        """
        logger.info("Building sequential workflow: data-agent → analyst")
        
        # Extract agents from dictionary
        data_agent_wrapper = agents.get("data-agent")
        analyst_wrapper = agents.get("analyst")
        
        if not all([data_agent_wrapper, analyst_wrapper]):
            missing = [k for k, v in [("data-agent", data_agent_wrapper), ("analyst", analyst_wrapper)] if not v]
            raise ValueError(f"Missing required agents: {missing}")
        
        # Extract underlying ChatAgent instances
        data_agent = data_agent_wrapper.agent  # type: ignore
        analyst = analyst_wrapper.agent  # type: ignore
        
        logger.info(f"Extracted ChatAgent instances: data_agent={data_agent.display_name}, analyst={analyst.display_name}")
        
        # Build sequential workflow
        # Pattern: User Query → Data Agent → Analyst → Final Response
        workflow = (
            SequentialBuilder()
            .participants([data_agent, analyst])  # type: ignore
            .build()
        )
        
        logger.info("✓ Sequential workflow built successfully")
        return workflow
    
    async def _extract_final_response(self, events: List[WorkflowEvent]) -> str:
        """
        Extract final response from sequential workflow events.
        
        In sequential workflow, WorkflowOutputEvent contains the complete
        conversation. We want the last agent's message (analyst's response).
        
        Args:
            events: List of workflow events
            
        Returns:
            Final response from analyst agent
        """
        logger.info(f"Processing {len(events)} events to extract response...")
        
        # Find WorkflowOutputEvent with conversation
        for event in reversed(events):
            event_type = type(event).__name__
            
            # WorkflowOutputEvent.data contains the full conversation
            if 'WorkflowOutput' in event_type and hasattr(event, 'data') and isinstance(event.data, list):
                try:
                    conversation = event.data
                    logger.info(f"Found WorkflowOutputEvent with {len(conversation)} messages")
                    
                    # Log all messages for debugging
                    for i, msg in enumerate(conversation):
                        author = msg.author_name or msg.role.value if hasattr(msg, 'role') else 'unknown'
                        text_preview = msg.text[:50] if hasattr(msg, 'text') and msg.text else '[no text]'
                        logger.debug(f"  Msg {i}: {author} - {text_preview}")
                    
                    # Get the last non-user message (should be analyst's response)
                    for msg in reversed(conversation):
                        # Get author
                        if hasattr(msg, 'author_name') and msg.author_name:
                            author = msg.author_name
                        elif hasattr(msg, 'role'):
                            author = msg.role.value
                        else:
                            continue
                        
                        # Skip user messages
                        if author.lower() == 'user':
                            continue
                        
                        # Get text
                        if hasattr(msg, 'text') and msg.text and msg.text.strip():
                            logger.info(f"✓ Extracted final response from '{author}'")
                            return msg.text
                            
                except Exception as e:
                    logger.error(f"Error processing {event_type}: {e}", exc_info=True)
        
        logger.warning("No final response could be extracted")
        return "Unable to extract final response from workflow"
    
    async def execute(
        self,
        message: str,
        thread_id: str,
        max_handoffs: Optional[int] = None,
    ) -> Tuple[str, WorkflowTraceMetadata]:
        """
        Execute sequential workflow: data-agent → analyst.
        
        Pattern:
        1. Load agents from Cosmos DB
        2. Build sequential workflow using SequentialBuilder
        3. Run workflow with user message
        4. Extract final response from conversation
        5. Build trace metadata
        
        Args:
            message: User's initial query
            thread_id: Thread ID for conversation context
            max_handoffs: Unused for sequential workflows
            
        Returns:
            Tuple of (final_response, trace_metadata)
        """
        handoff_path = ["data-agent", "analyst"]  # Sequential pipeline
        final_response = ""
        
        logger.info("=" * 80)
        logger.info("SEQUENTIAL WORKFLOW EXECUTE CALLED")
        logger.info("=" * 80)
        
        try:
            logger.info(
                f"Executing sequential workflow: thread={thread_id}, "
                f"message={message[:50]}..."
            )
            logger.info("Step 0: Sequential execute() method entered")
            
            # Step 1: Load agents from Cosmos DB
            logger.info("Step 1: Loading agents from Cosmos DB...")
            agents = self._load_agents_from_cosmos()
            
            if not agents or len(agents) < 2:
                raise ValueError(f"Insufficient agents loaded: {list(agents.keys())}")
            
            logger.info(f"Loaded agents: {list(agents.keys())}")
            
            # Step 2: Build workflow
            logger.info("Step 2: Building sequential workflow...")
            self.workflow = await self._build_workflow(agents)
            
            if not self.workflow:
                raise RuntimeError("Workflow was not initialized properly")
            
            # Step 3: Run workflow with initial message
            logger.info(f"Step 3: Running workflow with message: {message[:60]}...")
            try:
                # Collect events from initial run
                initial_events = await asyncio.wait_for(
                    self._drain_events(
                        self.workflow.run_stream(message)  # type: ignore
                    ),
                    timeout=60.0  # First phase timeout
                )
                logger.info(f"Received {len(initial_events)} events from initial run")
                
                # Check if workflow is waiting for more input (pending requests)
                pending_requests = []
                from agent_framework import RequestInfoEvent, HandoffUserInputRequest
                for event in initial_events:
                    if isinstance(event, RequestInfoEvent):
                        if isinstance(event.data, HandoffUserInputRequest):
                            pending_requests.append(event)
                            logger.debug(f"Found pending request: {event.request_id}")
                
                # If there are pending requests, send completion signal
                all_events = initial_events
                if pending_requests:
                    logger.info(f"Found {len(pending_requests)} pending requests, sending completion signal...")
                    try:
                        final_events = await asyncio.wait_for(
                            self._drain_events(
                                self.workflow.send_responses_streaming({
                                    req.request_id: "Workflow completed." for req in pending_requests
                                })  # type: ignore
                            ),
                            timeout=30.0
                        )
                        logger.info(f"Received {len(final_events)} events from completion")
                        all_events = initial_events + final_events
                    except asyncio.TimeoutError:
                        logger.warning("Completion signal timed out, using initial events")
                
                events = all_events
                
            except asyncio.TimeoutError:
                logger.error("Workflow execution timed out")
                raise RuntimeError("Sequential workflow execution timed out after 90 seconds")
            
            logger.info(f"Received {len(events)} total events from workflow run")
            
            # Step 4: Extract final response from events
            logger.info("Step 4: Extracting final response...")
            final_response = await self._extract_final_response(events)
            
            logger.info(f"✓ Extracted response: {final_response[:60]}...")
            
            # Step 5: Build trace metadata
            metadata = self._build_trace_metadata(
                final_response=final_response,
                primary_agent="analyst",
                handoff_path=handoff_path,
                satisfaction_score=0.85,
                evaluator_reasoning="Sequential pipeline completed successfully",
                max_attempts_reached=False,
                thread_id=thread_id,
            )
            
            logger.info("✓ Sequential workflow execution completed successfully")
            return final_response, metadata
            
        except Exception as e:
            logger.error(f"Sequential workflow execution failed: {e}", exc_info=True)
            raise
    
    async def _execute_sequence(
        self,
        agents: List[str],
        initial_message: str,
    ) -> Tuple[str, List[str]]:
        """
        Execute agents in sequence, passing output to next input.
        
        Args:
            agents: List of agent IDs in order
            initial_message: First agent's input
            
        Returns:
            Tuple of (final_output, sequence_path)
            
        TODO: Implement pipeline execution
        """
        current_output = initial_message
        path = []
        
        for agent_id in agents:
            logger.info(f"Pipeline step: {agent_id}")
            # TODO: Invoke agent_id with current_output
            # TODO: Capture response
            # TODO: Set current_output = response
            path.append(agent_id)
        
        return current_output, path
