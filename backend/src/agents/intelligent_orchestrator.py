"""
Intelligent multi-agent orchestration with evaluator pattern.

This implements a three-tier workflow:
1. Router: Classifies user intent and routes to appropriate specialist
2. Specialists: Data Agent, Analyst Agent, Order Agent handle domain-specific tasks
3. Evaluator: Assesses if response satisfies user query, recommends follow-up if needed

Routing Flow:
    User Query
        ↓
    [ROUTER] (classify intent)
        ↓
    [DATA-AGENT/ANALYST/ORDER-AGENT/MICROSOFT-DOCS] (execute)
        ↓
    [EVALUATOR] (assess satisfaction + generate JSON decision)
        ↓ (if satisfied)
    Return to User
        ↓ (if not satisfied)
    [ROUTER] (with evaluator context + recommended agent)
        ↓
    [NEXT SPECIALIST]
        ↓
    Back to [EVALUATOR]

Max Handoffs: 3 (prevents infinite loops)
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from agent_framework import ChatMessage
from agent_framework.azure import AzureOpenAIChatClient

logger = logging.getLogger(__name__)


@dataclass
class EvaluatorDecision:
    """Decision from the evaluator agent"""
    satisfied: bool
    reasoning: str
    confidence: float
    recommended_next_agent: Optional[str]


class IntelligentOrchestrator:
    """
    Manages multi-agent orchestration with quality evaluation.
    
    Uses HandoffBuilder to define the routing graph:
    - Router can route to any specialist
    - All specialists route to evaluator
    - Evaluator routes back to router if unsatisfied, or terminates if satisfied
    """
    
    def __init__(self, chat_client: AzureOpenAIChatClient):
        """
        Initialize orchestrator with Azure OpenAI client.
        
        Args:
            chat_client: AzureOpenAIChatClient instance
        """
        self.chat_client = chat_client
        self.workflow = None
        self.router_agent = None
        self.data_agent = None
        self.analyst_agent = None
        self.order_agent = None
        self.evaluator_agent = None
        self.microsoft_docs_agent = None
        
        logger.info("IntelligentOrchestrator initialized")
    
    def create_agents(self):
        """Create all specialist agents and evaluator."""
        logger.info("Creating specialist agents...")
        
        # Load prompts
        with open("src/agents/prompts/router_prompt.txt", "r") as f:
            router_instructions = f.read()
        
        with open("src/agents/prompts/data_agent_prompt.txt", "r") as f:
            data_instructions = f.read()
        
        with open("src/agents/prompts/analyst_agent_prompt.txt", "r") as f:
            analyst_instructions = f.read()
        
        with open("src/agents/prompts/order_agent_prompt.txt", "r") as f:
            order_instructions = f.read()
        
        with open("src/agents/prompts/evaluator_prompt.txt", "r") as f:
            evaluator_instructions = f.read()
        
        with open("src/agents/prompts/microsoft_docs_agent_prompt.txt", "r") as f:
            docs_instructions = f.read()
        
        # Create agents
        self.router_agent = self.chat_client.create_agent(
            instructions=router_instructions,
            name="router"
        )
        
        self.data_agent = self.chat_client.create_agent(
            instructions=data_instructions,
            name="data-agent"
        )
        
        self.analyst_agent = self.chat_client.create_agent(
            instructions=analyst_instructions,
            name="analyst"
        )
        
        self.order_agent = self.chat_client.create_agent(
            instructions=order_instructions,
            name="order-agent"
        )
        
        self.evaluator_agent = self.chat_client.create_agent(
            instructions=evaluator_instructions,
            name="evaluator"
        )
        
        self.microsoft_docs_agent = self.chat_client.create_agent(
            instructions=docs_instructions,
            name="microsoft-docs"
        )
        
        logger.info("✓ All agents created successfully")
    
    def build_workflow(self):
        """Build the HandoffBuilder workflow with routing configuration."""
        logger.info("Building HandoffBuilder workflow...")
        
        if not self.router_agent:
            raise RuntimeError("Agents not created. Call create_agents() first.")
        
        # Define the routing graph
        self.workflow = (
            HandoffBuilder(
                name="intelligent_support_workflow",
                participants=[
                    self.router_agent,
                    self.data_agent,
                    self.analyst_agent,
                    self.order_agent,
                    self.microsoft_docs_agent,
                    self.evaluator_agent,
                ],
            )
            # Router is the coordinator (entry point)
            .set_coordinator(self.router_agent)
            
            # Router can route to any specialist based on intent
            .add_handoff(self.router_agent, [
                self.data_agent,
                self.analyst_agent,
                self.order_agent,
                self.microsoft_docs_agent,
            ])
            
            # All specialists route to evaluator for quality assessment
            .add_handoff(self.data_agent, self.evaluator_agent)
            .add_handoff(self.analyst_agent, self.evaluator_agent)
            .add_handoff(self.order_agent, self.evaluator_agent)
            .add_handoff(self.microsoft_docs_agent, self.evaluator_agent)
            
            # Evaluator routes back to router if unsatisfied
            # (if satisfied, workflow terminates)
            .add_handoff(self.evaluator_agent, self.router_agent)
            
            # Termination: When evaluator indicates satisfaction
            .with_termination_condition(
                lambda conv: self._check_evaluator_satisfaction(conv)
            )
            
            .build()
        )
        
        logger.info("✓ Workflow built successfully")
    
    @staticmethod
    def _check_evaluator_satisfaction(conversation: List[ChatMessage]) -> bool:
        """
        Check if the evaluator has indicated satisfaction in the last message.
        
        Args:
            conversation: Full conversation history
            
        Returns:
            True if evaluator indicated satisfied=true, False otherwise
        """
        if not conversation:
            return False
        
        last_message = conversation[-1]
        
        # Check if this is from the evaluator
        if last_message.author_name != "evaluator":
            return False
        
        try:
            # Parse evaluator's JSON response
            response_text = last_message.text.strip()
            decision = json.loads(response_text)
            satisfied = decision.get("satisfied", False)
            
            if satisfied:
                logger.info("✓ Evaluator satisfied - terminating workflow")
                return True
            else:
                recommended = decision.get("recommended_next_agent")
                logger.info(f"⤴ Evaluator unsatisfied - routing to {recommended}")
                return False
        
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse evaluator response: {e}")
            return False
    
    async def run_workflow(self, user_message: str) -> tuple[str, Optional[str]]:
        """
        Run the workflow for a user query.
        
        Args:
            user_message: User's query
            
        Returns:
            Tuple of (final_response, primary_agent_used)
        """
        if not self.workflow:
            raise RuntimeError("Workflow not built. Call build_workflow() first.")
        
        logger.info(f"🚀 Starting workflow for query: {user_message[:50]}...")
        
        # Initial run with user query
        events = await self._drain(self.workflow.run_stream(user_message))
        pending_requests = self._handle_events(events)
        
        # Continue workflow if there are pending requests (user input needed)
        while pending_requests:
            logger.info(f"⏸ Workflow waiting for user input")
            # In API context, this would return and wait for next user message
            break
        
        # Extract final response
        final_response = self._extract_final_response(events)
        primary_agent = self._extract_primary_agent(events)
        
        logger.info(f"✓ Workflow completed")
        return final_response, primary_agent
    
    @staticmethod
    async def _drain(stream) -> list[WorkflowEvent]:
        """Collect all events from an async stream into a list."""
        return [event async for event in stream]
    
    @staticmethod
    def _handle_events(events: list[WorkflowEvent]) -> list[RequestInfoEvent]:
        """Process workflow events and extract pending user input requests."""
        requests: list[RequestInfoEvent] = []
        
        for event in events:
            if isinstance(event, WorkflowStatusEvent):
                logger.debug(f"[STATUS] {event.state.name}")
            elif isinstance(event, WorkflowOutputEvent):
                logger.debug(f"[OUTPUT] Message from {event.data}")
            elif isinstance(event, WorkflowUserInputRequest):
                requests.append(event)
                logger.info(f"[INPUT_REQUEST] Awaiting user input")
        
        return requests
    
    @staticmethod
    def _extract_final_response(events: list[WorkflowEvent]) -> str:
        """Extract the final response from workflow events."""
        for event in reversed(events):
            if isinstance(event, WorkflowOutputEvent):
                conversation = cast(list[ChatMessage], event.data)
                if conversation:
                    # Get the last non-evaluator message (final response to user)
                    for msg in reversed(conversation):
                        if msg.author_name != "evaluator":
                            return msg.text
        
        return "I was unable to process your request. Please try again."
    
    @staticmethod
    def _extract_primary_agent(events: list[WorkflowEvent]) -> Optional[str]:
        """Extract the primary specialist agent that was used."""
        for event in events:
            if isinstance(event, WorkflowOutputEvent):
                conversation = cast(list[ChatMessage], event.data)
                for msg in conversation:
                    # Find the first specialist agent (not router or evaluator)
                    if msg.author_name in ["data-agent", "analyst", "order-agent", "microsoft-docs"]:
                        return msg.author_name
        
        return None


async def create_orchestrator(chat_client: AzureOpenAIChatClient) -> IntelligentOrchestrator:
    """
    Factory function to create and initialize an orchestrator.
    
    Args:
        chat_client: AzureOpenAIChatClient instance
        
    Returns:
        Initialized IntelligentOrchestrator ready to run workflows
    """
    orchestrator = IntelligentOrchestrator(chat_client)
    orchestrator.create_agents()
    orchestrator.build_workflow()
    return orchestrator
