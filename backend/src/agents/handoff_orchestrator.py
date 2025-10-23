"""
Handoff orchestration pattern for multi-agent routing.

This implements an optimized handoff pattern inspired by Microsoft's OpenAI Workshop:
- Intent classification to determine which specialist agent should handle the request
- Direct user-to-specialist communication (no middleware)
- Handoff detection when agent response indicates request is outside their domain
- Context preservation when transferring between agents
- Lazy classification option for efficiency

Architecture:
1. First message: Classify intent and route to correct specialist
2. User communicates directly with specialist
3. Specialist detects "outside my area" requests and signals handoff
4. Router re-classifies and transfers to new specialist with context
5. Cycle repeats as needed
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from agent_framework import ChatMessage, Role

logger = logging.getLogger(__name__)


# ============================================================================
# Domain Definitions
# ============================================================================

class IntentClassificationResult(BaseModel):
    """Result of intent classification"""
    domain: str = Field(description="Target domain/specialist agent ID")
    is_domain_change: bool = Field(description="Whether this is a change from current domain")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0.0-1.0")
    reasoning: str = Field(description="Explanation of classification")


SPECIALIST_DOMAINS = {
    "sql-agent": {
        "name": "SQL Query Agent",
        "description": "Handles database queries, schema exploration, and data retrieval",
        "keywords": ["database", "table", "query", "sql", "schema", "data"],
        "handoff_phrase": "This is outside my area. Let me connect you with the right specialist.",
    },
    "azure-ops": {
        "name": "Azure Operations Agent",
        "description": "Handles Azure resources, deployments, and infrastructure",
        "keywords": ["azure", "resource", "deployment", "infrastructure", "cloud", "kubernetes"],
        "handoff_phrase": "This is outside my area. Let me connect you with the right specialist.",
    },
    "support-triage": {
        "name": "Support Triage Agent",
        "description": "Handles support tickets, troubleshooting, and documentation search",
        "keywords": ["support", "ticket", "help", "troubleshoot", "error", "problem", "documentation"],
        "handoff_phrase": "This is outside my area. Let me connect you with the right specialist.",
    },
    "data-analytics": {
        "name": "Data Analytics Agent",
        "description": "Handles analytics, insights, trends, and business intelligence",
        "keywords": ["analytics", "insight", "trend", "report", "dashboard", "metrics", "business"],
        "handoff_phrase": "This is outside my area. Let me connect you with the right specialist.",
    },
}


# ============================================================================
# Intent Classification Prompt
# ============================================================================

INTENT_CLASSIFIER_SYSTEM_PROMPT = """You are an expert intent classifier for a multi-agent system.

Available specialist agents:
1. sql-agent: Database queries, tables, schemas, data retrieval
2. azure-ops: Azure resources, deployments, infrastructure, cloud operations
3. support-triage: Support tickets, troubleshooting, error resolution, documentation
4. data-analytics: Analytics, insights, trends, business intelligence, reports

Your task: Analyze the user's message and determine which specialist should handle it.

Return a JSON object with:
{
  "domain": "sql-agent|azure-ops|support-triage|data-analytics",
  "is_domain_change": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}

Rules:
- If message is ambiguous, assign with lower confidence (0.3-0.6)
- If current domain still fits, keep same domain with is_domain_change=false
- If user explicitly requests different help, set is_domain_change=true
- For first message (current_domain=null), always set is_domain_change=true
"""


class HandoffOrchestrator:
    """
    Orchestrates multi-agent handoff routing with intent classification.
    
    Manages:
    - Intent classification for routing queries to correct agent
    - Handoff detection when agent response signals "outside my area"
    - Context preservation across agent handoffs
    - Session state for tracking current agent and conversation history
    """
    
    def __init__(self, session_id: str, state_store: Optional[Dict[str, Any]] = None):
        """
        Initialize orchestrator for a session.
        
        Args:
            session_id: Unique session identifier
            state_store: Optional dict to persist state across calls
        """
        self.session_id = session_id
        self.state_store = state_store or {}
        
        # Get current domain from state
        self._current_domain: Optional[str] = self.state_store.get(
            f"{session_id}_current_domain", None
        )
        
        # Conversation history
        self._chat_history: List[Dict[str, str]] = self.state_store.get(
            f"{session_id}_chat_history", []
        )
        
        # Turn counter
        self._turn: int = self.state_store.get(f"{session_id}_turn", 0)
        
        logger.info(
            f"[HANDOFF] Initialized orchestrator for session {session_id}, "
            f"current_domain={self._current_domain}"
        )
    
    @property
    def current_domain(self) -> Optional[str]:
        """Get current specialist domain"""
        return self._current_domain
    
    @property
    def chat_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self._chat_history
    
    def save_state(self):
        """Persist orchestrator state to state_store"""
        self.state_store[f"{self.session_id}_current_domain"] = self._current_domain
        self.state_store[f"{self.session_id}_chat_history"] = self._chat_history
        self.state_store[f"{self.session_id}_turn"] = self._turn
    
    async def classify_intent(self, user_message: str, llm_client=None) -> IntentClassificationResult:
        """
        Classify user intent and determine target domain.
        
        Args:
            user_message: The user's message
            llm_client: Azure OpenAI client for structured output
            
        Returns:
            IntentClassificationResult with domain, is_domain_change, confidence, reasoning
        """
        # If no LLM client, do simple keyword matching
        if not llm_client:
            logger.info("[HANDOFF] No LLM client, using keyword-based classification")
            return await self._keyword_based_classification(user_message)
        
        # Use LLM for classification with structured output
        try:
            logger.debug(f"[HANDOFF] Using LLM for intent classification, current_domain={self._current_domain}")
            
            prompt = f"""Current domain: {self._current_domain}
User message: {user_message}

Classify which specialist agent should handle this request."""
            
            # Try to use structured output
            try:
                from openai import AsyncAzureOpenAI
                
                # Assuming llm_client has necessary config
                client = llm_client
                
                # For now, use simple LLM call without structured output
                # Full implementation would use beta.chat.completions.parse()
                completion = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                
                response_text = completion.choices[0].message.content
                logger.debug(f"[HANDOFF] LLM classification response: {response_text}")
                
                # Parse JSON response
                result_dict = json.loads(response_text)
                result = IntentClassificationResult(**result_dict)
                logger.info(f"[HANDOFF] LLM classified to domain={result.domain}, confidence={result.confidence}")
                return result
                
            except Exception as e:
                logger.warning(f"[HANDOFF] LLM classification failed: {e}, falling back to keyword matching")
                return await self._keyword_based_classification(user_message)
                
        except Exception as e:
            logger.error(f"[HANDOFF] Error in intent classification: {e}", exc_info=True)
            # Fallback: stay with current domain or default to sql-agent
            default_domain = self._current_domain or "sql-agent"
            return IntentClassificationResult(
                domain=default_domain,
                is_domain_change=self._current_domain is None,
                confidence=0.3,
                reasoning=f"Classification error: {str(e)}"
            )
    
    async def _keyword_based_classification(self, user_message: str) -> IntentClassificationResult:
        """
        Simple keyword-based intent classification.
        
        Args:
            user_message: The user's message
            
        Returns:
            IntentClassificationResult
        """
        message_lower = user_message.lower()
        
        # Score each domain by keyword matches
        domain_scores: Dict[str, int] = {domain: 0 for domain in SPECIALIST_DOMAINS}
        
        for domain, config in SPECIALIST_DOMAINS.items():
            for keyword in config["keywords"]:
                if keyword in message_lower:
                    domain_scores[domain] += 1
        
        # Find best matching domain
        best_domain = max(domain_scores, key=lambda d: domain_scores[d])
        best_score = domain_scores[best_domain]
        
        # Calculate confidence based on score
        total_score = sum(domain_scores.values())
        confidence = (best_score / total_score) if total_score > 0 else 0.3
        
        # Determine if this is a domain change
        is_domain_change = (best_domain != self._current_domain) if self._current_domain else True
        
        result = IntentClassificationResult(
            domain=best_domain,
            is_domain_change=is_domain_change,
            confidence=min(confidence, 0.9),  # Cap at 0.9 for keyword matching
            reasoning=f"Keyword match: {best_score} matches for {best_domain}"
        )
        
        logger.info(f"[HANDOFF] Keyword classification: {best_domain} (confidence={result.confidence})")
        return result
    
    def detect_handoff_request(self, agent_response: str) -> bool:
        """
        Detect if agent response contains handoff request.
        
        Agents are instructed to use the phrase:
        "This is outside my area. Let me connect you with the right specialist."
        
        Args:
            agent_response: The agent's response text
            
        Returns:
            True if handoff marker detected, False otherwise
        """
        # Look for the exact handoff phrase or similar patterns
        patterns = [
            "outside my area",
            "connect you with",
            "specialist",
            "outside my domain",
            "outside my expertise",
        ]
        
        response_lower = agent_response.lower()
        detected = any(pattern in response_lower for pattern in patterns)
        
        if detected:
            logger.info(f"[HANDOFF] Handoff marker detected in agent response")
        
        return detected
    
    async def route_to_specialist(self, user_message: str) -> Dict[str, Any]:
        """
        Determine which specialist should handle the user's message.
        
        Args:
            user_message: The user's message
            
        Returns:
            Dict with keys:
            - specialist_id: ID of specialist agent
            - specialist_name: Name of specialist agent
            - is_domain_change: Whether this is a routing change
            - context_prefix: Optional context to prepend to prompt for handoff
        """
        # Classify intent
        intent = await self.classify_intent(user_message)
        target_domain = intent.domain
        is_domain_change = intent.is_domain_change
        
        logger.info(
            f"[HANDOFF] Route decision: {self._current_domain} -> {target_domain}, "
            f"domain_change={is_domain_change}, confidence={intent.confidence}"
        )
        
        # Build context prefix if this is a handoff
        context_prefix = None
        if is_domain_change and self._current_domain:
            context_prefix = self._build_context_prefix(self._current_domain, target_domain)
        
        # Update current domain
        self._current_domain = target_domain
        self._turn += 1
        self.save_state()
        
        return {
            "specialist_id": target_domain,
            "specialist_name": SPECIALIST_DOMAINS[target_domain]["name"],
            "is_domain_change": is_domain_change,
            "context_prefix": context_prefix,
            "confidence": intent.confidence,
            "reasoning": intent.reasoning
        }
    
    def _build_context_prefix(self, from_domain: str, to_domain: str) -> Optional[str]:
        """
        Build context prefix for handoff to preserve conversation.
        
        Args:
            from_domain: Previous specialist domain
            to_domain: Target specialist domain
            
        Returns:
            Context prefix to prepend to user message, or None if no history
        """
        if not self._chat_history:
            return None
        
        # Get last few turns for context (last 4 messages = 2 turns)
        recent_history = self._chat_history[-4:] if len(self._chat_history) >= 4 else self._chat_history
        
        # Build context string
        context_parts = ["[HANDOFF CONTEXT]"]
        context_parts.append(
            f"The user was just speaking with {SPECIALIST_DOMAINS[from_domain]['name']}."
        )
        context_parts.append("Recent conversation:")
        
        for msg in recent_history:
            role = msg.get("role", "unknown").title()
            content = msg.get("content", "")[:200]  # Truncate long messages
            context_parts.append(f"  {role}: {content}")
        
        context_parts.append(f"[END CONTEXT]\n")
        
        context_prefix = "\n".join(context_parts)
        logger.debug(f"[HANDOFF] Built context prefix: {len(context_prefix)} chars")
        
        return context_prefix
    
    def append_to_history(self, user_message: str, assistant_response: str):
        """
        Add user and assistant messages to chat history.
        
        Args:
            user_message: User's message
            assistant_response: Agent's response
        """
        self._chat_history.append({"role": "user", "content": user_message})
        self._chat_history.append({"role": "assistant", "content": assistant_response})
        self.save_state()
        logger.debug(f"[HANDOFF] Chat history updated: {len(self._chat_history)} messages")
