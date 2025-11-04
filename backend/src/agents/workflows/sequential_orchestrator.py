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
from agent_framework.observability import setup_observability, OBSERVABILITY_SETTINGS
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

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
        self.span_exporter: Optional[InMemorySpanExporter] = None
        self.tracer_provider: Optional[TracerProvider] = None
        
        # Required agents for sequential flow
        self.required_agents = [
            "data-agent",       # Retrieves data from database
            "analyst",          # Analyzes retrieved data
        ]
        
        # Initialize observability for tool call capture
        self._setup_observability()
    
    def _setup_observability(self) -> None:
        """
        Set up OpenTelemetry observability to capture tool calls.
        
        Tool calls are automatically traced by agent-framework when observability is enabled.
        We set up an in-memory span exporter to capture these traces for later extraction.
        """
        try:
            # Enable observability in agent-framework
            OBSERVABILITY_SETTINGS.enable_otel = True
            OBSERVABILITY_SETTINGS.enable_sensitive_data = True  # Capture tool arguments/results
            
            # Create in-memory span exporter to capture traces
            self.span_exporter = InMemorySpanExporter()
            
            # Create tracer provider with our exporter
            self.tracer_provider = TracerProvider()
            self.tracer_provider.add_span_processor(SimpleSpanProcessor(self.span_exporter))
            
            # Set as global tracer provider
            trace.set_tracer_provider(self.tracer_provider)
            
            logger.info("✓ Observability enabled for tool call capture")
            
        except Exception as e:
            logger.warning(f"Failed to setup observability: {e}. Tool calls will not be captured.")
            self.span_exporter = None
            self.tracer_provider = None
    
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
            
            # Step 4: Extract agent interactions from events for detailed traces
            logger.info("Step 4a: Extracting agent interactions for traces...")
            print(f"🔍 ABOUT TO EXTRACT AGENT INTERACTIONS FROM {len(events)} EVENTS")
            self._extract_agent_interactions(events, message)
            print(f"🔍 FINISHED EXTRACTING INTERACTIONS: {len(self.interactions)} found")
            
            # Step 4b: Extract final response from events
            logger.info("Step 4b: Extracting final response...")
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
            
            # Debug: Log metadata to verify tool calls are included
            logger.info(f"✓ Built trace metadata with {len(metadata.agent_interactions)} interactions")
            for interaction in metadata.agent_interactions:
                logger.info(f"  - {interaction.agent_id}: {len(interaction.tool_calls)} tool calls")
                if interaction.tool_calls:
                    for tc in interaction.tool_calls:
                        logger.info(f"    * {tc.get('name')}: args={tc.get('arguments', 'N/A')[:50]}")
            
            logger.info("✓ Sequential workflow execution completed successfully")
            return final_response, metadata
            
        except Exception as e:
            logger.error(f"Sequential workflow execution failed: {e}", exc_info=True)
            raise
    
    def _extract_tool_calls_from_traces(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls for a specific agent from OpenTelemetry traces.
        
        Tool calls are automatically captured by agent-framework's observability system
        as separate spans with 'gen_ai.operation.name' = 'execute_tool'.
        
        NOTE: This method extracts and CLEARS spans, so each agent only gets the tool
        calls that occurred during its execution. Call this immediately after each
        agent completes.
        
        Args:
            agent_id: The agent ID to find tool calls for
            
        Returns:
            List of tool call dictionaries with name, arguments, result, duration
        """
        if not self.span_exporter:
            logger.debug("No span exporter available - tool calls not captured")
            return []
        
        tool_calls = []
        
        try:
            # Get all finished spans from the exporter
            spans = self.span_exporter.get_finished_spans()
            
            logger.debug(f"Checking {len(spans)} spans for tool calls from {agent_id}")
            
            for span in spans:
                # Look for tool execution spans
                # These have gen_ai.operation.name = 'execute_tool'
                attrs = span.attributes or {}
                
                operation_name = attrs.get('gen_ai.operation.name')
                if operation_name == 'execute_tool':
                    # This is a tool execution span
                    tool_name = attrs.get('gen_ai.tool.name', 'unknown')
                    tool_call_id = attrs.get('gen_ai.tool.call.id', 'unknown')
                    # Note: The attribute is gen_ai.tool.call.arguments, not gen_ai.tool.arguments
                    tool_args = attrs.get('gen_ai.tool.call.arguments', '{}')
                    
                    # Try multiple possible attribute names for the result
                    tool_result_raw = (
                        attrs.get('gen_ai.tool.call.result') or
                        attrs.get('gen_ai.tool.result') or
                        attrs.get('tool.result') or
                        attrs.get('function.result')
                    )
                    
                    # Debug: Log all attributes to see what's available
                    if tool_name == 'read_data':
                        logger.info(f"🔍 read_data span attributes: {list(attrs.keys())}")
                        for key, value in attrs.items():
                            if 'result' in key.lower() or 'output' in key.lower():
                                logger.info(f"  🔍 {key}: {str(value)[:200]}")
                        
                        # Also check span events
                        if hasattr(span, 'events') and span.events:
                            logger.info(f"🔍 read_data span has {len(span.events)} events")
                            for event in span.events:
                                logger.info(f"  🔍 Event: {event.name}")
                                if hasattr(event, 'attributes') and event.attributes:
                                    for k, v in event.attributes.items():
                                        logger.info(f"    🔍 {k}: {str(v)[:200]}")
                    
                    tool_duration_attr = attrs.get('agent_framework.function.invocation.duration', 0)
                    
                    # Convert tool result to a serializable string representation
                    tool_result = None
                    if tool_result_raw is not None:
                        try:
                            # Check if it's already marked as non-serializable
                            if isinstance(tool_result_raw, str) and 'non-serializable' in tool_result_raw.lower():
                                tool_result = None  # Don't show the placeholder
                            else:
                                # Try to convert to string with length limit
                                result_str = str(tool_result_raw)
                                # Limit to 500 characters for display
                                if len(result_str) > 500:
                                    tool_result = result_str[:500] + '... (truncated)'
                                else:
                                    tool_result = result_str
                        except Exception:
                            tool_result = None
                    
                    # Use the duration from attributes if available, otherwise calculate from span times
                    try:
                        # The attribute value should be a float (seconds)
                        tool_duration_seconds = float(tool_duration_attr) if tool_duration_attr else 0  # type: ignore
                        if tool_duration_seconds > 0:
                            duration_ms = tool_duration_seconds * 1000  # Convert seconds to milliseconds
                        else:
                            duration_ns = 0
                            if span.end_time and span.start_time:
                                duration_ns = span.end_time - span.start_time
                            duration_ms = float(duration_ns) / 1_000_000
                    except (ValueError, TypeError):
                        duration_ms = 0.0
                    
                    tool_call = {
                        'id': tool_call_id,
                        'name': tool_name,
                        'arguments': tool_args,
                        'result': tool_result,
                        'duration_ms': round(duration_ms, 2)
                    }
                    
                    tool_calls.append(tool_call)
                    logger.debug(f"Found tool call: {tool_name} (duration: {duration_ms:.2f}ms)")
            
            # Clear the spans after extraction so the next agent doesn't see these tool calls
            self.span_exporter.clear()
            
            logger.info(f"Extracted {len(tool_calls)} tool calls for {agent_id}, cleared spans")
            
        except Exception as e:
            logger.warning(f"Error extracting tool calls from traces: {e}", exc_info=True)
        
        return tool_calls
    
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
            path.append(agent_id)
            # TODO: Invoke agent_id with current_output
            # TODO: Capture response
            # TODO: Set current_output = response
        
        return current_output, path
    
    def _extract_agent_interactions(self, events: List[Any], initial_message: str) -> None:
        """
        Extract agent interactions from workflow events for detailed trace display.
        
        Parses workflow events to identify individual agent calls, their inputs/outputs,
        tool calls, and timing information. Populates self.interactions for trace metadata.
        
        Args:
            events: List of workflow events from SequentialBuilder execution
            initial_message: The original user message that started the workflow
        """
        from src.agents.workflows.workflow_models import AgentInteraction
        
        logger.info(f"Processing {len(events)} workflow events to extract agent interactions...")
        
        current_agent = None
        current_input = initial_message
        current_tool_calls = []
        interaction_start_time = 0
        agent_messages = []  # Collect streaming messages for each agent
        
        for i, event in enumerate(events):
            event_type = type(event).__name__
            
            # Track agent execution boundaries
            if event_type == 'ExecutorInvokedEvent' and hasattr(event, 'executor_id'):
                executor_id = str(event.executor_id)
                # Filter out non-agent executors
                if not executor_id.startswith('to-conversation:') and executor_id not in ['input-conversation', 'end']:
                    if current_agent is not None and agent_messages:
                        # Save previous agent's interaction
                        self._save_agent_interaction(current_agent, current_input, agent_messages, current_tool_calls, interaction_start_time, i)
                        agent_messages = []
                        current_tool_calls = []
                    
                    current_agent = executor_id
                    interaction_start_time = i
                    logger.info(f"Started tracking agent: {executor_id}")
            
            # Collect agent streaming messages
            elif event_type == 'AgentRunUpdateEvent' and hasattr(event, 'executor_id') and hasattr(event, 'data'):
                executor_id = str(event.executor_id)
                data_obj = getattr(event, 'data', '')
                message_content = str(data_obj)
                
                if current_agent and executor_id == current_agent:
                    # Collect ALL message parts, including empty ones (they're part of the streaming)
                    agent_messages.append(message_content)
            
            # Capture tool call events (these are rare with agent-framework, as tools are traced via OpenTelemetry)
            elif 'ToolCall' in event_type or 'Tool' in event_type and 'Call' in event_type:
                if current_agent and hasattr(event, 'data'):
                    tool_data = event.data
                    tool_call = {
                        'name': getattr(tool_data, 'name', None) or getattr(tool_data, 'tool_name', 'unknown_tool'),
                        'input': getattr(tool_data, 'arguments', None) or getattr(tool_data, 'parameters', {}),
                        'output': None,  # Will be filled by tool response
                        'timestamp': getattr(event, 'timestamp', i)
                    }
                    current_tool_calls.append(tool_call)
            
            # Capture tool response events  
            elif 'ToolResponse' in event_type or ('Tool' in event_type and 'Response' in event_type):
                if current_agent and current_tool_calls and hasattr(event, 'data'):
                    tool_response = event.data
                    # Match this response to the last tool call
                    if current_tool_calls:
                        response_content = getattr(tool_response, 'content', None) or getattr(tool_response, 'result', str(tool_response))
                        current_tool_calls[-1]['output'] = response_content
            
            # Handle agent completion
            elif event_type == 'ExecutorCompletedEvent' and hasattr(event, 'executor_id'):
                executor_id = str(event.executor_id)
                if current_agent == executor_id and current_agent is not None:
                    if agent_messages:
                        # Save the completed agent's interaction
                        self._save_agent_interaction(current_agent, current_input, agent_messages, current_tool_calls, interaction_start_time, i)
                        
                        # The full agent output becomes input for next agent
                        full_output = ''.join(agent_messages).strip()
                        if full_output:
                            current_input = full_output
                    
                    agent_messages = []
                    current_tool_calls = []
        
        # Handle any remaining agent interaction
        if current_agent is not None and agent_messages:
            self._save_agent_interaction(current_agent, current_input, agent_messages, current_tool_calls, interaction_start_time, len(events))
        
        logger.info(f"✓ Extracted {len(self.interactions)} agent interactions for trace display")
    
    def _save_agent_interaction(self, agent_id: str, input_text: str, message_parts: List[str], tool_calls: List[dict], start_time: int, end_time: int) -> None:
        """Save an agent interaction from collected message parts."""
        from src.agents.workflows.workflow_models import AgentInteraction
        
        # Combine all message parts to get the full output
        full_output = ''.join(message_parts).strip()
        
        if not full_output or len(full_output) < 5:  # Skip empty or very short outputs
            print(f"🔍 SKIPPING INTERACTION: {agent_id} - output too short ({len(full_output)} chars)")
            return
        
        # Calculate execution time (rough estimate)
        execution_time = (end_time - start_time) * 100  # Fallback timing
        
        # Extract tool calls from OpenTelemetry traces
        # This captures the actual tool executions that were traced by agent-framework
        extracted_tool_calls = self._extract_tool_calls_from_traces(agent_id)
        
        # Use extracted tool calls if available, otherwise fall back to tool_calls parameter
        final_tool_calls = extracted_tool_calls if extracted_tool_calls else (tool_calls.copy() if tool_calls else [])
        
        # Debug: Log the tool calls structure
        print(f"🔍 TOOL CALLS FOR {agent_id}:")
        for idx, tc in enumerate(final_tool_calls):
            print(f"🔍   [{idx}] Type: {type(tc)}, Keys: {tc.keys() if isinstance(tc, dict) else 'N/A'}")
            print(f"🔍       Data: {tc}")
        
        # Create agent interaction
        interaction = AgentInteraction(
            agent_id=agent_id,
            input=input_text,
            output=full_output,
            tool_calls=final_tool_calls,
            execution_time_ms=execution_time
        )
        
        self.interactions.append(interaction)
        print(f"🔍 SAVED INTERACTION: {agent_id} - {len(full_output)} chars, {len(final_tool_calls)} tool calls, input: {input_text[:50]}...")
        logger.info(f"✓ Captured interaction for {agent_id}: {len(full_output)} chars, {len(final_tool_calls)} tool calls")
