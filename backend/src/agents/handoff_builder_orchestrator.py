"""
Intelligent multi-agent orchestration using Microsoft Agent Framework's HandoffBuilder.

This orchestrator loads existing agents from the database and uses HandoffBuilder
to configure sophisticated multi-tier routing:

1. Router: Classifies user intent and routes to appropriate specialist
2. Specialists: Data Agent, Analyst Agent, Order Agent, Microsoft Docs (from Cosmos DB)
3. Evaluator: Assesses satisfaction and recommends follow-up if needed

Routing Graph:
    User → Router → Specialists
                      ↓
                    Evaluator
                    ↓    ↓
              (satisfied) (unsatisfied)
                ↓          ↓
              User     Router (with context)
                          ↓
                    Next Specialist

Uses HandoffBuilder to configure the multi-tier routing explicitly.
All agents are loaded from the database, not created inline.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterable
from typing import cast, Optional

from agent_framework import (
    ChatMessage,
    HandoffBuilder,
    WorkflowEvent,
    WorkflowRunState,
    WorkflowStatusEvent,
    WorkflowOutputEvent,
)
from agent_framework.azure import AzureOpenAIChatClient

from src.persistence.agents import get_agent_repository
from src.agents.factory import AgentFactory

logger = logging.getLogger(__name__)


class HandoffBuilderOrchestrator:
    """
    Multi-agent orchestrator using HandoffBuilder from Agent Framework.
    
    Loads existing agents from database and manages intelligent routing 
    between specialists with quality evaluation.
    """
    
    def __init__(self, chat_client: AzureOpenAIChatClient):
        """
        Initialize orchestrator.
        
        Args:
            chat_client: AzureOpenAIChatClient instance
        """
        self.chat_client = chat_client
        self.agent_repo = None
        self.workflow = None
        self.agents = {}
        self.required_agents = [
            "router",
            "data-agent",
            "analyst",
            "order-agent",
            "microsoft-docs",
            "evaluator",
        ]
        
        logger.info("HandoffBuilderOrchestrator initialized")
    
    async def load_agents(self) -> None:
        """Load all specialist agents from database."""
        logger.info("Loading specialist agents from database...")
        
        # Get repository
        self.agent_repo = get_agent_repository()
        
        # Load each agent from database
        for agent_id in self.required_agents:
            try:
                # Get agent metadata from Cosmos DB
                agent_config = self.agent_repo.get(agent_id)
                
                if not agent_config:
                    raise RuntimeError(f"Required agent '{agent_id}' not found in database")
                
                # Create agent instance using factory
                agent = AgentFactory.create_from_metadata(agent_config)
                
                if not agent:
                    raise RuntimeError(f"Failed to create agent instance for '{agent_id}'")
                
                self.agents[agent_id] = agent
                logger.info(f"✓ Loaded agent: {agent_id}")
                
            except Exception as e:
                logger.error(f"Failed to load agent '{agent_id}': {e}")
                raise
        
        logger.info(f"✓ All {len(self.agents)} agents loaded from database")
    
    
    async def build_workflow(self) -> None:
        """Build the HandoffBuilder workflow with routing configuration."""
        if not self.agents:
            raise RuntimeError("Agents not loaded. Call load_agents() first.")
        
        logger.info("Building HandoffBuilder workflow...")
        
        # Get agent instances
        router = self.agents["router"]
        data_agent = self.agents["data-agent"]
        analyst = self.agents["analyst"]
        order_agent = self.agents["order-agent"]
        microsoft_docs = self.agents["microsoft-docs"]
        evaluator = self.agents["evaluator"]
        
        # Define the multi-tier routing graph
        self.workflow = (
            HandoffBuilder(
                name="intelligent_support_workflow",
                participants=[
                    router,
                    data_agent,
                    analyst,
                    order_agent,
                    microsoft_docs,
                    evaluator,
                ],
            )
            # Router is the entry point (coordinator)
            .set_coordinator(router)
            
            # Router can handoff to any specialist
            .add_handoff(
                router,
                [data_agent, analyst, order_agent, microsoft_docs]
            )
            
            # All specialists handoff to evaluator for quality assessment
            .add_handoff(data_agent, evaluator)
            .add_handoff(analyst, evaluator)
            .add_handoff(order_agent, evaluator)
            .add_handoff(microsoft_docs, evaluator)
            
            # Evaluator can handoff back to router if unsatisfied
            .add_handoff(evaluator, router)
            
            # Termination condition: Check if evaluator indicated satisfaction
            .with_termination_condition(
                lambda conversation: self._check_satisfaction(conversation)
            )
            
            .build()
        )
        
        logger.info("✓ Workflow built successfully")
    
    @staticmethod
    def _check_satisfaction(conversation: list[ChatMessage]) -> bool:
        """
        Check if evaluator indicated satisfaction (query fully addressed).
        
        The evaluator responds with JSON containing "satisfied": true/false.
        Workflow terminates when satisfied=true.
        
        Args:
            conversation: Full conversation history
            
        Returns:
            True if evaluator indicated satisfaction, False otherwise
        """
        if not conversation:
            return False
        
        # Find the last message from evaluator
        for message in reversed(conversation):
            if message.author_name == "evaluator":
                try:
                    # Parse evaluator's JSON response
                    response_text = message.text.strip()
                    decision = json.loads(response_text)
                    
                    if decision.get("satisfied", False):
                        logger.info("✓ Evaluator satisfied - workflow terminating")
                        return True
                    else:
                        recommended = decision.get("recommended_next_agent", "unknown")
                        logger.info(f"⤴ Evaluator unsatisfied - routing to {recommended}")
                        return False
                
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    logger.warning(f"Could not parse evaluator response: {e}")
                    # Assume satisfied on parse error to avoid infinite loops
                    return True
        
        return False
    
    async def run_workflow(
        self,
        user_message: str,
        max_turns: int = 10
    ) -> tuple[str, Optional[str]]:
        """
        Execute the workflow for a user query.
        
        Args:
            user_message: User's initial query
            max_turns: Maximum conversation turns before terminating
            
        Returns:
            Tuple of (final_response, primary_specialist_used)
        """
        if not self.workflow:
            raise RuntimeError("Workflow not built. Call build_workflow() first.")
        
        logger.info(f"🚀 Starting workflow: {user_message[:60]}...")
        
        try:
            # Start the workflow with user message
            events = await self._drain(self.workflow.run_stream(user_message))
            pending_requests = self._handle_events(events)
            
            turn = 0
            while pending_requests and turn < max_turns:
                turn += 1
                logger.info(f"[WORKFLOW-TURN-{turn}] Workflow waiting for user input (not expected in automated mode)")
                
                # In a real API, this is where we'd get user's next message
                # For now, break to avoid hanging
                break
            
            # Extract final response and primary specialist
            final_response = self._extract_final_response(events)
            primary_specialist = self._extract_primary_specialist(events)
            
            logger.info(f"✓ Workflow completed")
            return final_response, primary_specialist
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def _drain(stream: AsyncIterable[WorkflowEvent]) -> list[WorkflowEvent]:
        """Collect all events from async stream."""
        return [event async for event in stream]
    
    @staticmethod
    def _handle_events(events: list[WorkflowEvent]) -> list:
        """Process workflow events and extract pending requests."""
        requests = []
        
        for event in events:
            if isinstance(event, WorkflowStatusEvent):
                logger.debug(f"[STATUS] {event.state.name}")
                if event.state == WorkflowRunState.IDLE_WITH_PENDING_REQUESTS:
                    logger.info("⏸ Workflow has pending user input")
            elif isinstance(event, WorkflowOutputEvent):
                logger.debug(f"[OUTPUT] Conversation update")
        
        return requests
    
    @staticmethod
    def _extract_final_response(events: list[WorkflowEvent]) -> str:
        """Extract the final response from workflow events."""
        final_response = None
        
        for event in reversed(events):
            if isinstance(event, WorkflowOutputEvent):
                conversation = cast(list[ChatMessage], event.data)
                if conversation:
                    # Get the last non-evaluator message (final response to user)
                    for msg in reversed(conversation):
                        # Skip evaluator messages and router routing messages
                        if msg.author_name and msg.author_name not in ["evaluator", "router"]:
                            return msg.text
                    
                    # If we only have router/evaluator messages, get the last specialist
                    for msg in reversed(conversation):
                        if msg.author_name and msg.author_name not in ["evaluator"]:
                            final_response = msg.text
                            break
                    
                    if final_response:
                        return final_response
        
        return "I was unable to process your request. Please try again."
    
    @staticmethod
    def _extract_primary_specialist(events: list[WorkflowEvent]) -> Optional[str]:
        """Extract the primary specialist agent that handled the query."""
        for event in events:
            if isinstance(event, WorkflowOutputEvent):
                conversation = cast(list[ChatMessage], event.data)
                for msg in conversation:
                    # Find the first specialist agent (not router or evaluator)
                    if msg.author_name in ["data-agent", "analyst", "order-agent", "microsoft-docs"]:
                        return msg.author_name
        
        return None


async def create_handoff_orchestrator(
    chat_client: AzureOpenAIChatClient,
) -> HandoffBuilderOrchestrator:
    """
    Factory function to create and initialize a HandoffBuilder orchestrator.
    
    Args:
        chat_client: AzureOpenAIChatClient instance
        
    Returns:
        Fully initialized orchestrator ready to run workflows
    """
    orchestrator = HandoffBuilderOrchestrator(chat_client)
    await orchestrator.load_agents()
    await orchestrator.build_workflow()
    return orchestrator
