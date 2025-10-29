"""
Agent Seeding
Seeds default agents into Cosmos DB on application startup.

Streamlined Agent Architecture:
1. Router Agent - Active, intelligent multi-agent orchestrator
2. Data Agent - Active, unified database query specialist
3. Analyst Agent - Active, business intelligence and insights
4. Order Agent - Active, order placement and fulfillment
5. Microsoft Docs Agent - Active, documentation search

All agents are focused, specialized, and work together via handoff pattern.
"""
import logging
from typing import List
from pathlib import Path
from src.persistence.agents import get_agent_repository
from src.persistence.models import AgentMetadata, AgentStatus, ToolType, ToolConfig

logger = logging.getLogger(__name__)

# Path to agent prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "agents" / "prompts"


def load_prompt(prompt_filename: str) -> str:
    """
    Load a prompt from the prompts directory.
    
    Args:
        prompt_filename: Name of the prompt file (e.g., "sales_agent_prompt.txt")
    
    Returns:
        Prompt text content
    
    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = PROMPTS_DIR / prompt_filename
    
    if not prompt_path.exists():
        logger.warning(f"Prompt file not found: {prompt_path}, using fallback")
        return f"You are a helpful assistant. (Prompt file {prompt_filename} not found)"
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Failed to load prompt from {prompt_path}: {e}")
        return f"You are a helpful assistant. (Error loading {prompt_filename})"


def get_default_agents() -> List[AgentMetadata]:
    """
    Define default agents to seed into the database.
    
    Returns:
        List of AgentMetadata objects representing default agents
    """
    return [
        # 1. Router Agent (ACTIVE) - Multi-agent orchestrator
        AgentMetadata(
            id="router",
            name="Router Agent",
            description="Intelligent multi-agent orchestrator. Routes complex queries to specialists via intent classification and handoff pattern.",
            system_prompt=load_prompt("router_prompt.txt"),
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4000,
            max_messages=25,
            tools=[],
            capabilities=[
                "intent_classification",
                "handoff_orchestration",
                "multi_agent_coordination",
                "query_routing"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="2.0.0"
        ),
        
        # 2. Data Agent (ACTIVE) - Unified database query specialist
        AgentMetadata(
            id="data-agent",
            name="Data Agent",
            description="Single source of truth for all Wide World Importers database queries. Handles sales, inventory, purchasing, finance, and customer data.",
            system_prompt=load_prompt("data_agent_prompt.txt"),
            model="gpt-4o",
            temperature=0.6,
            max_tokens=4000,
            max_messages=20,
            tools=[
                ToolConfig(
                    type=ToolType.MCP,
                    name="mssql-mcp",
                    mcp_server_name="mssql-mcp",
                    config={"description": "SQL database access for Wide World Importers"},
                    enabled=True
                )
            ],
            capabilities=[
                "sales_analysis",
                "inventory_management",
                "purchasing_analytics",
                "financial_reporting",
                "customer_insights",
                "cross_domain_queries"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 3. Analyst Agent (ACTIVE) - Business intelligence and insights
        AgentMetadata(
            id="analyst",
            name="Analyst Agent",
            description="Transforms data into business insights. Analyzes trends, provides recommendations, and generates strategic guidance based on data from the Data Agent.",
            system_prompt=load_prompt("analyst_agent_prompt.txt"),
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4000,
            max_messages=20,
            tools=[],
            capabilities=[
                "trend_analysis",
                "performance_analysis",
                "comparative_analysis",
                "opportunity_identification",
                "financial_insights",
                "forecasting",
                "recommendations"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 4. Order Agent (ACTIVE) - Order placement and fulfillment
        AgentMetadata(
            id="order-agent",
            name="Order Agent",
            description="Wide World Importers order specialist. Handles order placement, order confirmation, and order validation. Works with data provided by the Data Agent.",
            system_prompt=load_prompt("order_agent_prompt.txt"),
            model="gpt-4o",
            temperature=0.6,
            max_tokens=3000,
            max_messages=15,
            tools=[],
            capabilities=[
                "order_placement",
                "order_confirmation",
                "order_modification",
                "order_validation"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 5. Microsoft Docs Agent (ACTIVE) - Documentation search
        AgentMetadata(
            id="microsoft-docs",
            name="Microsoft Docs Agent",
            description="Searches Microsoft Learn documentation and provides technical guidance. Helps find relevant articles, code samples, and best practices.",
            system_prompt=load_prompt("microsoft_docs_agent_prompt.txt"),
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4000,
            max_messages=20,
            tools=[
                ToolConfig(
                    type=ToolType.MCP,
                    name="microsoft-learn",
                    mcp_server_name="microsoft-learn-mcp",
                    config={"description": "Search Microsoft Learn documentation"},
                    enabled=True
                )
            ],
            capabilities=[
                "documentation_search",
                "technical_guidance",
                "code_samples",
                "api_reference",
                "best_practices"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
    ]


def seed_agents() -> dict:
    """
    Seed default agents into the database (IDEMPOTENT).
    
    This function only creates agents if they don't already exist.
    It does NOT update existing agents, allowing runtime modifications
    (like activating agents or attaching custom tools) to persist.
    
    This makes seed_agents() safe to call on every startup without
    overwriting user changes.
    
    Returns:
        Dictionary with seeding statistics:
        - created: Number of agents created
        - skipped: Number of agents skipped (already exist)
        - total: Total number of default agents
    """
    repo = get_agent_repository()
    agents = get_default_agents()
    
    created = 0
    skipped = 0
    updated = 0
    
    for agent in agents:
        try:
            # Check if agent already exists
            existing = repo.get(agent.id)
            
            if existing:
                # Special case: Router Agent should have no tools (A2A fix)
                # If it exists but still has tools, update it to remove them
                if agent.id == "router" and len(existing.tools) > 0:
                    logger.info(f"Router Agent found with tools, updating to remove them: {agent.id}")
                    logger.info(f"  Previous tools: {len(existing.tools)}, New tools: {len(agent.tools)}")
                    # Update the agent to remove tools
                    existing.tools = agent.tools
                    existing.system_prompt = agent.system_prompt
                    existing.capabilities = agent.capabilities
                    repo.upsert(existing)
                    logger.info(f"Updated Router Agent to remove A2A tools: {agent.id}")
                    updated += 1
                # Special case: SQL Agent should have custom tool
                # If it exists but has no tools, update it
                elif agent.id == "sql-agent" and len(existing.tools) == 0 and len(agent.tools) > 0:
                    logger.info(f"SQL Agent found with missing tools, updating: {agent.id}")
                    logger.info(f"  Previous tools: {len(existing.tools)}, New tools: {len(agent.tools)}")
                    # Update the agent with the tools from the seed definition
                    existing.tools = agent.tools
                    repo.upsert(existing)
                    logger.info(f"Updated SQL Agent with custom tool: {agent.id}")
                    updated += 1
                else:
                    logger.info(f"Agent already exists, skipping (preserving runtime changes): {agent.id}")
                    logger.info(f"  Current status: {existing.status.value}, Existing tools: {len(existing.tools)}")
                    skipped += 1
            else:
                logger.info(f"Agent not found, creating new: {agent.id}")
                # Only create if doesn't exist - don't overwrite
                repo.upsert(agent)
                logger.info(f"Created agent: {agent.id} ({agent.name}) - Status: {agent.status.value}")
                created += 1
                
        except Exception as e:
            logger.error(f"Failed to seed agent {agent.id}: {e}")
            # Continue with other agents
    
    result = {
        "created": created,
        "skipped": skipped,
        "updated": updated,
        "total": len(agents)
    }
    
    logger.info(f"Agent seeding complete: {created} created, {skipped} skipped, {updated} updated, {len(agents)} total")
    return result


def list_seeded_agents() -> List[AgentMetadata]:
    """
    List all agents that match the default agent IDs.
    Useful for verification after seeding.
    
    Returns:
        List of AgentMetadata for default agents
    """
    repo = get_agent_repository()
    default_ids = {agent.id for agent in get_default_agents()}
    
    agents = []
    for agent_id in default_ids:
        agent = repo.get(agent_id)
        if agent:
            agents.append(agent)
    
    return agents


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Seed agents
    result = seed_agents()
    print(f"\n✅ Seeding complete:")
    print(f"   Created: {result['created']}")
    print(f"   Skipped: {result['skipped']}")
    print(f"   Total: {result['total']}")
    
    # List seeded agents
    print(f"\n📋 Seeded agents:")
    agents = list_seeded_agents()
    for agent in agents:
        status_emoji = "✅" if agent.status == AgentStatus.ACTIVE else "⏸️"
        print(f"   {status_emoji} {agent.id}: {agent.name} ({agent.status.value})")
