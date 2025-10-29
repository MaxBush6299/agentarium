"""
Handoff Router for multi-agent orchestration.

This module implements the handoff orchestration pattern for routing user queries
to specialist agents based on intent classification, with support for handoff
requests when an agent encounters an out-of-domain query.

Key Features:
- Intent-based routing: Classifies user intent and routes to appropriate specialist
- Handoff detection: Monitors agent responses for handoff requests
- Context preservation: Maintains conversation history across handoffs
- Lazy evaluation: Can classify intent on-demand or upfront
- Multi-turn support: Handles conversations spanning multiple agents

Pattern:
1. Classify user intent to determine target specialist
2. Load specialist agent with appropriate tools
3. Route message to specialist agent
4. Collect response
5. Detect if handoff is needed (agent says "outside my area")
6. If handoff needed: re-classify, load new specialist, repeat from step 3

Usage:
    ```python
    router = HandoffRouter(agent_repo)
    target_agent, context_prefix = await router.route_to_specialist(user_message)
    
    # Run specialist agent
    response = await target_agent.run(user_message, thread=agent_thread)
    
    # Check for handoff
    needs_handoff = router.detect_handoff_request(response)
    if needs_handoff:
        # Re-route to different specialist
        new_agent, context = await router.route_to_specialist(user_message)
        response = await new_agent.run(context + user_message, thread=agent_thread)
    ```
"""

from typing import Optional, Tuple, Any, Dict, List
import logging
import re

from src.agents.handoff_orchestrator import HandoffOrchestrator, IntentClassificationResult
from src.agents.factory import AgentFactory
from src.agents.base import DemoBaseAgent
from src.persistence.models import AgentMetadata

logger = logging.getLogger(__name__)


class HandoffRouter:
    """
    Routes user messages to specialist agents based on intent classification.
    
    This router manages the handoff pattern:
    - Classifies intent on each message (can be lazy: skip upfront, check response)
    - Loads appropriate specialist agent with tools
    - Detects handoff requests in responses
    - Manages context transfer between agents
    
    Attributes:
        agent_repo: Repository for loading agent metadata
        orchestrator: HandoffOrchestrator instance for intent classification
        specialist_agents: Cache of loaded specialist agents {agent_id: DemoBaseAgent}
        conversation_history: Multi-turn conversation tracking
    """
    
    # Specialist agent metadata
    SPECIALIST_DOMAINS = {
        "data-agent": {
            "name": "Data Agent",
            "keywords": [
                "inventory", "stock", "customer", "order", "sales", "supplier", "payment", 
                "data", "show", "list", "get", "query", "search", "retrieve", "find",
                "information", "details", "records", "table", "database", "statistics",
                "count", "total", "sum", "average", "report"
            ]
        },
        "analyst": {
            "name": "Analyst Agent",
            "keywords": [
                "analyze", "analysis", "trend", "insight", "recommend", "recommendation", 
                "forecast", "performance", "best", "worst", "top", "bottom", "pattern",
                "opportunity", "risk", "summary", "overview", "why", "how", "impact",
                "strategy", "plan", "improve", "optimize"
            ]
        },
        "order-agent": {
            "name": "Order Agent",
            "keywords": [
                "order", "place", "purchase", "buy", "checkout", "confirm", "ship", 
                "delivery", "submit", "create", "new order", "book", "reserve",
                "fulfillment", "process order", "place an order"
            ]
        },
        "microsoft-docs": {
            "name": "Microsoft Docs Agent",
            "keywords": [
                "microsoft", "documentation", "docs", "how to", "tutorial", "api",
                "reference", "learn", "guide", "manual", "instructions", "example", "azure"
            ]
        }
    }
    
    # Handoff markers that indicate agent wants to redirect to another agent
    HANDOFF_MARKERS = [
        r"outside my area",
        r"outside my expertise",
        r"not my responsibility",
        r"not my domain",
        r"let me connect you",
        r"let me route you",
        r"let me transfer you",
        r"i should transfer",
        r"would be better suited",
        r"more appropriate",
        r"seems more like a",
        r"sounds like a.*question",
        r"doesn't seem right for",
        r"wrong specialist",
    ]
    
    def __init__(self, agent_repo, session_id: str):
        """
        Initialize HandoffRouter.
        
        Args:
            agent_repo: Repository for loading agent metadata
            session_id: Unique session identifier for orchestrator state
        """
        self.agent_repo = agent_repo
        self.session_id = session_id
        self.orchestrator = HandoffOrchestrator(session_id=session_id)
        self.specialist_agents: Dict[str, DemoBaseAgent] = {}
        self.current_domain: Optional[str] = None  # Track current specialist domain
        
        logger.info(f"HandoffRouter initialized for session {session_id}")
    
    async def route_to_specialist(
        self,
        user_message: str,
        use_lazy_classification: bool = False
    ) -> Tuple[Optional[str], Optional[DemoBaseAgent], str]:
        """
        Route user message to appropriate specialist agent.
        
        This method:
        1. Classifies user intent (unless lazy_classification is True)
        2. Loads specialist agent matching the intent
        3. Returns target agent_id, agent instance, and context prefix
        
        Args:
            user_message: The user's message to classify and route
            use_lazy_classification: If True, skip classification (return None for agent_id)
                                    This means: let agent respond first, check response for handoff
            
        Returns:
            Tuple of (target_agent_id, agent_instance, context_prefix)
            - target_agent_id: ID of the target specialist (e.g., 'sql-agent')
            - agent_instance: Loaded DemoBaseAgent ready to chat
            - context_prefix: Text to prepend to message (includes history for handoff)
            
            Returns (None, None, "") if classification fails or agent can't be loaded
        """
        try:
            # Classify intent to determine target specialist
            classification = await self.orchestrator.classify_intent(user_message)
            
            if not classification or not classification.domain:
                logger.warning(f"Could not classify intent for message: {user_message[:50]}...")
                return None, None, ""
            
            target_agent_id = classification.domain
            logger.info(f"Classified intent to domain: {target_agent_id} (confidence: {classification.confidence})")
            
            # Load specialist agent
            agent = await self._get_specialist_agent(target_agent_id)
            
            if not agent:
                logger.error(f"Could not load specialist agent: {target_agent_id}")
                return None, None, ""
            
            # Build context prefix for multi-turn conversations (handoff scenario)
            context_prefix = ""
            if self.current_domain and self.current_domain != target_agent_id:
                # This is a handoff - build context from history
                context_prefix = self.orchestrator._build_context_prefix(
                    self.current_domain, target_agent_id
                ) or ""
            
            # Update current domain
            self.current_domain = target_agent_id
            
            return target_agent_id, agent, context_prefix
        
        except Exception as e:
            logger.error(f"Error routing to specialist: {type(e).__name__}: {e}", exc_info=False)
            return None, None, ""
    
    async def analyze_response_gaps(
        self,
        user_message: str,
        specialist_response: str,
        specialist_id: str,
        agents_consulted: List[str]
    ) -> Optional[str]:
        """
        Analyze if the specialist's response fully addresses the user's query.
        
        Uses LLM to detect if there are gaps or unanswered parts of the query that
        require consultation with another specialist.
        
        Args:
            user_message: Original user query
            specialist_response: Response from the specialist
            specialist_id: ID of the specialist who responded
            agents_consulted: List of agent IDs already consulted (to avoid loops)
            
        Returns:
            Next specialist ID if gaps detected, None if query fully addressed
        """
        try:
            # Build gap analysis prompt
            available_specialists = [
                agent_id for agent_id in self.SPECIALIST_DOMAINS.keys()
                if agent_id not in agents_consulted and agent_id != specialist_id
            ]
            
            if not available_specialists:
                logger.info("🔍 No more specialists available for gap analysis")
                return None
            
            specialist_list = "\n".join([
                f"- {agent_id}: {self.SPECIALIST_DOMAINS[agent_id]['name']}"
                for agent_id in available_specialists
            ])
            
            gap_analysis_prompt = f"""Analyze if the specialist's response fully addresses the user's query.

USER QUERY:
{user_message}

SPECIALIST RESPONSE (from {specialist_id}):
{specialist_response}

AVAILABLE SPECIALISTS:
{specialist_list}

TASK:
Determine if the user's query has been FULLY addressed, or if there are gaps/unanswered parts that require another specialist.

ANALYSIS RULES:
1. If the specialist provided DATA only but the user asked for ANALYSIS, trends, patterns, recommendations, or insights → needs analyst
2. If the specialist provided DATA but user asked to PLACE AN ORDER or take ACTION → needs order-agent
3. If the specialist provided raw data/tables but didn't explain what they mean → likely needs analyst
4. If the user explicitly asked "why", "what does this mean", "analyze", "trends", "recommendations", "should we", "what if" → needs analyst
5. If the specialist is data-agent and user's query contained analysis-related keywords → needs analyst for follow-up
6. If response is just data retrieval without answering the INTENT behind the question → gap exists

COMMON PATTERNS THAT INDICATE GAPS:
- Data agent returns tables → analyst should provide insights/patterns
- User asked "what's the trend" but only got data → gap
- User asked "are we doing well" but only got numbers → gap
- Data tables with no interpretation → gap
- User asked for a recommendation but only got data → gap

RESPONSE FORMAT:
If query is FULLY addressed:
{{"needs_handoff": false, "next_specialist": null, "reasoning": "Brief explanation"}}

If query has GAPS requiring another specialist:
{{"needs_handoff": true, "next_specialist": "agent-id-here", "reasoning": "Brief explanation of what's missing"}}

Respond with ONLY the JSON object, no other text."""

            # Call LLM for gap analysis
            from src.config import settings
            from openai import AsyncAzureOpenAI
            
            client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            response = await client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing conversational AI responses for completeness."},
                    {"role": "user", "content": gap_analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            if not result_text:
                logger.warning("Gap analysis returned empty response")
                return None
            
            result_text = result_text.strip()
            
            # Parse JSON response
            import json
            result = json.loads(result_text)
            
            if result.get("needs_handoff"):
                next_specialist = result.get("next_specialist")
                reasoning = result.get("reasoning", "")
                logger.info(f"🔍 Gap analysis: Handoff needed to {next_specialist}")
                logger.info(f"🔍 Reasoning: {reasoning}")
                return next_specialist
            else:
                reasoning = result.get("reasoning", "")
                logger.info(f"🔍 Gap analysis: Query fully addressed")
                logger.info(f"🔍 Reasoning: {reasoning}")
                return None
        
        except Exception as e:
            logger.error(f"Error in gap analysis: {type(e).__name__}: {e}", exc_info=False)
            return None
    
    async def _synthesize_responses(
        self,
        user_message: str,
        agent_responses: List[Dict[str, str]]
    ) -> str:
        """
        Synthesize multiple agent responses into a coherent final answer.
        
        Args:
            user_message: Original user query
            agent_responses: List of dicts with 'agent_id' and 'response' keys
            
        Returns:
            Synthesized response combining all agent insights
        """
        try:
            if len(agent_responses) == 1:
                # Only one response, return as-is
                return agent_responses[0]['response']
            
            # Build synthesis prompt
            responses_text = "\n\n".join([
                f"FROM {resp['agent_id']}:\n{resp['response']}"
                for resp in agent_responses
            ])
            
            synthesis_prompt = f"""Synthesize the following specialist responses into a single, coherent answer.

USER QUERY:
{user_message}

SPECIALIST RESPONSES:
{responses_text}

TASK:
Combine these responses into a comprehensive answer that:
1. Addresses all parts of the user's query
2. Flows naturally and logically
3. Avoids repetition
4. Maintains professional tone
5. Preserves important details and data from each specialist

Provide ONLY the synthesized response, no meta-commentary."""

            # Call LLM for synthesis
            from src.config import settings
            from openai import AsyncAzureOpenAI
            
            client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            response = await client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at synthesizing multi-agent responses into coherent answers."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            synthesized_content = response.choices[0].message.content
            if not synthesized_content:
                logger.warning("Synthesis returned empty response, using fallback")
                return "\n\n".join([resp['response'] for resp in agent_responses])
            
            synthesized = synthesized_content.strip()
            logger.info(f"📝 Synthesized response from {len(agent_responses)} agents")
            
            return synthesized
        
        except Exception as e:
            logger.error(f"Error synthesizing responses: {type(e).__name__}: {e}", exc_info=False)
            # Fallback: concatenate responses
            return "\n\n".join([resp['response'] for resp in agent_responses])
    
    async def route_and_chat(
        self,
        agent: Optional[DemoBaseAgent],
        user_message: str,
        agent_thread: Any,
        max_handoffs: int = 3,
        run_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
        """
        Route message through specialist agents, handling handoffs as needed.
        
        This is the main orchestration method that:
        1. Routes to appropriate specialist based on intent
        2. Runs specialist agent
        3. Detects if handoff is needed
        4. Re-routes if handoff detected (up to max_handoffs times)
        5. Returns final response and list of agents involved
        
        Args:
            agent: Router agent instance (not directly used, kept for API compatibility)
            user_message: The user's message
            agent_thread: Agent framework thread for maintaining state
            max_handoffs: Maximum number of handoffs to allow before returning response
            run_id: Optional run ID for querying step history
            thread_id: Optional thread ID for querying step history
            
        Returns:
            Tuple of (final_response_text, specialist_used, tool_calls)
            - final_response_text: Response from the final specialist
            - specialist_used: ID of specialist that provided final response
            - tool_calls: List of tool call dicts from all specialists involved
        """
        try:
            current_message = user_message
            response = None
            specialist_used = None
            handoff_count = 0
            all_tool_calls: List[Dict[str, Any]] = []
            agent_responses: List[Dict[str, str]] = []  # Track all specialist responses
            agents_consulted: List[str] = []  # Track which agents we've already consulted
            
            # Track if we've pre-selected a specialist via handoff
            preselected_agent_id: Optional[str] = None
            
            for turn in range(max_handoffs + 1):
                # If we have a pre-selected agent (from handoff), use it directly
                # Otherwise, classify intent and get specialist
                if preselected_agent_id:
                    logger.info(f"[HANDOFF-TURN-{turn}] Using pre-selected agent: {preselected_agent_id}")
                    specialist_agent = await self._get_specialist_agent(preselected_agent_id)
                    target_agent_id = preselected_agent_id
                    context_prefix = ""
                    preselected_agent_id = None  # Clear for next iteration
                else:
                    target_agent_id, specialist_agent, context_prefix = await self.route_to_specialist(
                        current_message,
                        use_lazy_classification=False
                    )
                
                if not specialist_agent:
                    logger.error(f"Could not load specialist agent, aborting handoff routing")
                    return "I'm sorry, I wasn't able to route your question to the right agent.", None, []
                
                specialist_used = target_agent_id
                logger.info(f"[HANDOFF-TURN-{turn}] Routing to {target_agent_id}")
                print(f"[HANDOFF-TURN-{turn}] Routing to {target_agent_id}")
                
                # Build message with context (for multi-turn conversations)
                full_message = (context_prefix + "\n\n" + current_message) if context_prefix else current_message
                
                # Run specialist agent with timeout
                try:
                    logger.info(f"[HANDOFF-TURN-{turn}] Executing {target_agent_id}.run()")
                    print(f"[HANDOFF-TURN-{turn}] Executing {target_agent_id}.run()")
                    
                    # Add timeout to prevent hanging
                    import asyncio
                    try:
                        response = await asyncio.wait_for(
                            specialist_agent.run(full_message, thread=agent_thread),
                            timeout=120.0  # 120 second timeout (2 minutes for complex queries with tools)
                        )
                    except asyncio.TimeoutError:
                        logger.error(f"[HANDOFF-TURN-{turn}] Agent {target_agent_id} timed out after 120 seconds")
                        print(f"[HANDOFF-TURN-{turn}] ⏱️ TIMEOUT: Agent {target_agent_id} took too long to respond")
                        return f"I'm sorry, the {target_agent_id} took too long to respond. Please try again.", target_agent_id, []
                    
                    logger.info(f"[HANDOFF-TURN-{turn}] Got response from {target_agent_id}")
                    print(f"[HANDOFF-TURN-{turn}] Got response from {target_agent_id}")
                    
                    # DEBUG: Check agent_thread for execution history
                    print(f"[HANDOFF-TURN-{turn}] Agent thread type: {type(agent_thread).__name__}")
                    if hasattr(agent_thread, '__dict__'):
                        print(f"[HANDOFF-TURN-{turn}] Agent thread attributes: {list(vars(agent_thread).keys())}")
                    if hasattr(agent_thread, 'history'):
                        print(f"[HANDOFF-TURN-{turn}] Agent thread history: {agent_thread.history}")
                    if hasattr(agent_thread, 'messages'):
                        print(f"[HANDOFF-TURN-{turn}] Agent thread messages count: {len(agent_thread.messages)}")
                        for i, msg in enumerate(agent_thread.messages[-5:]):  # Last 5 messages
                            print(f"[HANDOFF-TURN-{turn}]   Message {i}: {type(msg).__name__}")
                    
                    # Extract response text
                    response_text = self._extract_response_text(response)
                    
                    # Store this agent's response (only if we have a valid agent ID)
                    if target_agent_id:
                        agent_responses.append({
                            'agent_id': target_agent_id,
                            'response': response_text
                        })
                        agents_consulted.append(target_agent_id)
                    
                    # Extract tool calls from response structure (pass agent_thread for message_store access)
                    tool_calls = self._extract_tool_calls(response, agent_thread=agent_thread)
                    all_tool_calls.extend(tool_calls)
                    
                    # HYBRID HANDOFF DETECTION
                    # Mode 1: Check for explicit handoff signals
                    explicit_handoff = self.detect_handoff_request(response_text)
                    
                    if explicit_handoff:
                        logger.info(f"🔄 [HANDOFF-TURN-{turn}] Explicit handoff signal detected")
                        print(f"🔄 [HANDOFF-TURN-{turn}] Explicit handoff signal detected")
                        
                        if handoff_count < max_handoffs:
                            # Set next message to original user query (for re-classification)
                            current_message = user_message
                            handoff_count += 1
                            continue
                    
                    # Mode 2: Gap analysis - check if response fully addresses query
                    if handoff_count < max_handoffs and target_agent_id:
                        logger.info(f"🔍 [HANDOFF-TURN-{turn}] Running gap analysis...")
                        print(f"🔍 [HANDOFF-TURN-{turn}] Running gap analysis...")
                        
                        next_specialist = await self.analyze_response_gaps(
                            user_message=user_message,
                            specialist_response=response_text,
                            specialist_id=target_agent_id,
                            agents_consulted=agents_consulted
                        )
                        
                        if next_specialist:
                            logger.info(f"🔍 [HANDOFF-TURN-{turn}] Gap detected, routing to {next_specialist}")
                            print(f"🔍 [HANDOFF-TURN-{turn}] Gap detected, routing to {next_specialist}")
                            
                            # Override next routing to the suggested specialist
                            current_message = user_message
                            handoff_count += 1
                            agents_consulted.append(target_agent_id)
                            
                            # Pre-select the specialist for next iteration (skip route_to_specialist)
                            preselected_agent_id = next_specialist
                            continue
                    
                    # No handoff needed - finalize response
                    logger.info(f"🏁 [HANDOFF-TURN-{turn}] Query fully addressed by {len(agent_responses)} specialist(s)")
                    print(f"🏁 [HANDOFF-TURN-{turn}] Query fully addressed")
                    
                    # Synthesize if multiple specialists were consulted
                    if len(agent_responses) > 1:
                        logger.info(f"📝 [HANDOFF-TURN-{turn}] Synthesizing {len(agent_responses)} responses...")
                        print(f"📝 [HANDOFF-TURN-{turn}] Synthesizing responses...")
                        
                        final_response = await self._synthesize_responses(
                            user_message=user_message,
                            agent_responses=agent_responses
                        )
                        return final_response, specialist_used, all_tool_calls
                    else:
                        # Single specialist - return response as-is
                        return response_text, specialist_used, all_tool_calls
                
                except Exception as e:
                    logger.error(f"[HANDOFF-TURN-{turn}] Error running specialist: {type(e).__name__}: {e}", exc_info=False)
                    print(f"[HANDOFF-TURN-{turn}] Error: {e}")
                    return f"Error communicating with specialist: {str(e)}", specialist_used, all_tool_calls
            
            # If we get here, max handoffs exceeded
            logger.warning(f"Max handoffs ({max_handoffs}) exceeded, returning last response")
            response_text = self._extract_response_text(response) if response else "Unable to process request after multiple handoffs."
            return response_text, specialist_used, all_tool_calls
        
        except Exception as e:
            logger.error(f"Fatal error in route_and_chat: {type(e).__name__}: {e}", exc_info=True)
            return f"Error in handoff routing: {str(e)}", None, []
    
    def detect_handoff_request(self, response_text: str) -> bool:
        """
        Detect if agent is requesting a handoff to another specialist.
        
        Looks for patterns like:
        - "This is outside my area. Let me connect you with the right specialist."
        - "That seems more like a [domain] question"
        - etc.
        
        Args:
            response_text: Response from specialist agent
            
        Returns:
            True if handoff marker detected, False otherwise
        """
        if not response_text:
            return False
        
        response_lower = response_text.lower()
        
        # Check for handoff markers
        for marker in self.HANDOFF_MARKERS:
            if re.search(marker, response_lower):
                logger.info(f"Handoff detected via marker: {marker}")
                return True
        
        return False
    
    async def _get_specialist_agent(self, agent_id: str) -> Optional[DemoBaseAgent]:
        """
        Load specialist agent from repository.
        
        Uses caching to avoid reloading the same agent multiple times.
        
        Args:
            agent_id: ID of specialist agent (e.g., 'sql-agent')
            
        Returns:
            Loaded DemoBaseAgent or None if not found
        """
        # Check cache first
        if agent_id in self.specialist_agents:
            logger.debug(f"Using cached agent: {agent_id}")
            return self.specialist_agents[agent_id]
        
        try:
            # Load from repository
            agent_config = self.agent_repo.get(agent_id)
            
            if not agent_config:
                logger.error(f"Specialist agent not found: {agent_id}")
                return None
            
            # Create agent via factory
            agent = AgentFactory.create_from_metadata(agent_config)
            
            if not agent:
                logger.error(f"Failed to create specialist agent: {agent_id}")
                return None
            
            # Cache for future use
            self.specialist_agents[agent_id] = agent
            logger.info(f"Loaded specialist agent: {agent_id}")
            
            return agent
        
        except Exception as e:
            logger.error(f"Exception loading specialist agent {agent_id}: {type(e).__name__}: {e}", exc_info=False)
            return None
    
    def _extract_response_text(self, response: Any) -> str:
        """
        Extract text content from agent response.
        
        Handles multiple response types:
        - MessageResponse with messages array
        - Objects with text attribute
        - Plain strings
        
        Args:
            response: Response object from agent.run()
            
        Returns:
            Extracted text content
        """
        if not response:
            return ""
        
        # If it's already a string
        if isinstance(response, str):
            return response
        
        # If it has messages array (MessageResponse)
        if hasattr(response, 'messages') and response.messages:
            # Get the last assistant message
            for msg in reversed(response.messages):
                role = getattr(msg, 'role', None)
                if role is not None:
                    # Convert enum to string if needed
                    if hasattr(role, 'value'):
                        role_str = str(role.value)
                    else:
                        role_str = str(role)
                    
                    if role_str == 'assistant':
                        # Extract text content
                        if hasattr(msg, 'contents') and msg.contents:
                            for content in msg.contents:
                                if hasattr(content, 'text'):
                                    return content.text
                        if hasattr(msg, 'content'):
                            return msg.content
        
        # If it has a text attribute
        if hasattr(response, 'text'):
            return response.text
        
        # If it has content attribute
        if hasattr(response, 'content'):
            return response.content
        
        # Fallback: convert to string
        return str(response)
    
    def _extract_tool_calls(self, response: Any, agent_thread: Any = None) -> List[Dict[str, Any]]:
        """
        Extract tool calls from agent response.
        
        Looks through the messages for tool calls made by the assistant.
        Falls back to agent_thread._message_store if response messages don't have results.
        
        Args:
            response: Response object from agent.run()
            agent_thread: Optional agent_thread for accessing internal message store
            
        Returns:
            List of tool call dicts with name, args, result info
        """
        tool_calls: List[Dict[str, Any]] = []
        
        if not response:
            return tool_calls
        
        # If it has messages array (MessageResponse)
        if hasattr(response, 'messages') and response.messages:
            for msg_idx, msg in enumerate(response.messages):
                role = getattr(msg, 'role', None)
                
                if role is not None:
                    # Convert enum to string if needed
                    if hasattr(role, 'value'):
                        role_str = str(role.value)
                    else:
                        role_str = str(role)
                    
                    # Look for assistant messages with function call content
                    if role_str == 'assistant':
                        if hasattr(msg, 'contents') and msg.contents:
                            for content in msg.contents:
                                content_type = type(content).__name__
                                
                                # FunctionCallContent is what we're looking for
                                if content_type == 'FunctionCallContent':
                                    tool_name = getattr(content, 'name', 'unknown')
                                    tool_id = getattr(content, 'call_id', None)
                                    tool_args = getattr(content, 'arguments', '{}')
                                    
                                    # Parse arguments if it's a JSON string
                                    try:
                                        import json
                                        if isinstance(tool_args, str):
                                            tool_args_dict = json.loads(tool_args)
                                        else:
                                            tool_args_dict = tool_args
                                    except:
                                        tool_args_dict = tool_args
                                    
                                    tool_call = {
                                        'type': 'function_call',
                                        'name': tool_name,
                                        'id': tool_id,
                                        'arguments': tool_args_dict
                                    }
                                    tool_calls.append(tool_call)
                                    print(f"[_extract_tool_calls] Found FunctionCallContent: {tool_name}")
                    
                    # Look for tool result messages
                    elif role_str == 'tool':
                        if hasattr(msg, 'contents') and msg.contents:
                            for content in msg.contents:
                                content_type = type(content).__name__
                                
                                # TextContent with tool result
                                if content_type == 'TextContent':
                                    result_text = getattr(content, 'text', '')
                                    
                                    # Update last tool call with result
                                    if tool_calls and 'output' not in tool_calls[-1]:
                                        tool_calls[-1]['output'] = result_text
                                        # Try to parse as JSON if it looks like JSON
                                        try:
                                            import json
                                            parsed = json.loads(result_text)
                                            tool_calls[-1]['output_parsed'] = parsed
                                            print(f"[_extract_tool_calls] Added parsed result to last tool call")
                                        except:
                                            pass
                                        print(f"[_extract_tool_calls] Added result to last tool call: {len(result_text)} chars")
        
        # If no outputs found in response, try agent_thread._message_store
        if agent_thread and tool_calls and not any('output' in tc for tc in tool_calls):
            print(f"[_extract_tool_calls] No outputs in response, checking agent_thread._message_store")
            try:
                if hasattr(agent_thread, '_message_store'):
                    message_store = agent_thread._message_store
                    # The message store is a thread context that has messages
                    if hasattr(message_store, 'messages'):
                        messages = message_store.messages
                        print(f"[_extract_tool_calls] Found {len(messages)} messages in message_store")
                        
                        # DEBUG: Print all messages to understand structure
                        for msg_idx, msg in enumerate(messages):
                            role = getattr(msg, 'role', None)
                            msg_type = type(msg).__name__
                            if role is not None:
                                if hasattr(role, 'value'):
                                    role_str = str(role.value)
                                else:
                                    role_str = str(role)
                            else:
                                role_str = "unknown"
                            print(f"[_extract_tool_calls]   Message {msg_idx}: type={msg_type}, role={role_str}")
                            
                            # Check for contents or other attributes
                            if hasattr(msg, 'contents'):
                                print(f"[_extract_tool_calls]     Has contents: {len(msg.contents)} items")
                                for content_idx, content in enumerate(msg.contents):
                                    content_type = type(content).__name__
                                    print(f"[_extract_tool_calls]       Content {content_idx}: type={content_type}")
                                    if hasattr(content, 'text'):
                                        text_preview = str(getattr(content, 'text', ''))[:100]
                                        print(f"[_extract_tool_calls]         Text preview: {text_preview}")
                        
                        # Find tool result messages and match them to tool calls
                        # Track which tool calls have been filled
                        next_unfilled_idx = 0
                        
                        for msg in messages:
                            role = getattr(msg, 'role', None)
                            if role is not None:
                                if hasattr(role, 'value'):
                                    role_str = str(role.value)
                                else:
                                    role_str = str(role)
                                
                                if role_str == 'tool':
                                    if hasattr(msg, 'contents') and msg.contents:
                                        # Process each result content in order
                                        for content in msg.contents:
                                            content_type = type(content).__name__
                                            
                                            # Find next tool call without output
                                            while next_unfilled_idx < len(tool_calls) and 'output' in tool_calls[next_unfilled_idx]:
                                                next_unfilled_idx += 1
                                            
                                            if next_unfilled_idx >= len(tool_calls):
                                                print(f"[_extract_tool_calls] WARNING: More results than tool calls!")
                                                break
                                            
                                            # Handle FunctionResultContent (new format)
                                            if content_type == 'FunctionResultContent':
                                                # Extract the result from FunctionResultContent
                                                result_data = getattr(content, 'result', None)
                                                
                                                # Handle different result types
                                                result_text = ""
                                                
                                                if isinstance(result_data, str):
                                                    # Plain string result
                                                    result_text = result_data
                                                elif isinstance(result_data, list):
                                                    # List of content objects (e.g., TextContent)
                                                    text_parts = []
                                                    for item in result_data:
                                                        if hasattr(item, 'text'):
                                                            text_parts.append(str(item.text))
                                                        elif isinstance(item, str):
                                                            text_parts.append(item)
                                                        else:
                                                            text_parts.append(str(item))
                                                    result_text = "".join(text_parts)
                                                elif hasattr(result_data, 'text'):
                                                    # Single TextContent object - extract text
                                                    result_text = str(getattr(result_data, 'text', ''))
                                                elif isinstance(result_data, dict):
                                                    # Dictionary result - convert to JSON
                                                    import json
                                                    result_text = json.dumps(result_data)
                                                elif result_data is not None:
                                                    # Other object - convert to string
                                                    result_text = str(result_data)
                                                
                                                tool_calls[next_unfilled_idx]['output'] = result_text
                                                try:
                                                    import json
                                                    if isinstance(result_data, dict):
                                                        tool_calls[next_unfilled_idx]['output_parsed'] = result_data
                                                    else:
                                                        parsed = json.loads(result_text) if result_text else None
                                                        if parsed:
                                                            tool_calls[next_unfilled_idx]['output_parsed'] = parsed
                                                    print(f"[_extract_tool_calls] Added parsed result to tool {next_unfilled_idx} ({tool_calls[next_unfilled_idx]['name']})")
                                                except Exception as e:
                                                    print(f"[_extract_tool_calls] Could not parse result as JSON: {e}")
                                                print(f"[_extract_tool_calls] Added result to tool {next_unfilled_idx} ({tool_calls[next_unfilled_idx]['name']}): {len(result_text)} chars")
                                                next_unfilled_idx += 1
                                            
                                            # Handle TextContent (old format fallback)
                                            elif content_type == 'TextContent':
                                                result_text = getattr(content, 'text', '')
                                                
                                                tool_calls[next_unfilled_idx]['output'] = result_text
                                                try:
                                                    import json
                                                    parsed = json.loads(result_text)
                                                    tool_calls[next_unfilled_idx]['output_parsed'] = parsed
                                                    print(f"[_extract_tool_calls] Added parsed result to tool {next_unfilled_idx} ({tool_calls[next_unfilled_idx]['name']})")
                                                except:
                                                    pass
                                                print(f"[_extract_tool_calls] Added result to tool {next_unfilled_idx} ({tool_calls[next_unfilled_idx]['name']}): {len(result_text)} chars")
                                                next_unfilled_idx += 1
            except Exception as e:
                print(f"[_extract_tool_calls] Error accessing message_store: {e}")
        
        print(f"[_extract_tool_calls] Extracted {len(tool_calls)} tool calls total")
        for i, tc in enumerate(tool_calls):
            print(f"[_extract_tool_calls]   Tool {i}: {tc['name']}, has output: {'output' in tc}")
        return tool_calls
    
    def reset(self):
        """
        Reset router state for a new conversation.
        
        Clears agent cache and domain tracking. Orchestrator state preserved for session.
        """
        self.specialist_agents = {}
        self.current_domain = None
        logger.info(f"HandoffRouter reset for session {self.session_id}")
