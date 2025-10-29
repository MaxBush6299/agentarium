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

DEPRECATED: This module has been archived and replaced by the official
HandoffBuilder pattern in handoff_builder_orchestrator.py. This code is
kept for reference only.
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
    
    DEPRECATED: Use handoff_builder_orchestrator.py instead.
    
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
