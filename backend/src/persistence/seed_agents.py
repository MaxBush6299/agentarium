"""
Agent Seeding
Seeds default agents into Cosmos DB on application startup.

Default Agents:
1. Router Agent - Active, multi-agent orchestrator using A2A to call specialists
2. Support Triage Agent - Active, with MCP + OpenAPI tools
3. Azure Ops Agent - Active, with MCP + OpenAPI tools
4. SQL Agent - Active, with custom MCP tool for Adventure Works
5. Data Analytics Agent - Active, analyzes enterprise data and generates reports
6. Business Impact Agent - Inactive, placeholder for future development
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
        # 1. Router Agent (ACTIVE) - Multi-agent orchestrator using Handoff Pattern
        AgentMetadata(
            id="router",
            name="Router Agent",
            description="Intelligent multi-agent orchestrator using handoff pattern. Routes queries to specialists via intent classification.",
            system_prompt=load_prompt("router_prompt.txt"),
            model="gpt-4.1",
            temperature=0.7,
            max_tokens=4000,
            max_messages=25,
            tools=[],
            capabilities=[
                "intent_classification",
                "handoff_orchestration",
                "clarification",
                "guidance"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="2.0.0"
        ),
        
        # 2. Microsoft Docs Agent (ACTIVE)
        AgentMetadata(
            id="microsoft-docs",
            name="Microsoft Docs Agent",
            description="Searches Microsoft Learn documentation and provides technical guidance. Helps find relevant articles, code samples, and best practices.",
            system_prompt=load_prompt("microsoft_docs_agent_prompt.txt"),
            model="gpt-4.1",
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
                "api_reference"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 3. Sales Agent (ACTIVE - Wide World Importers)
        AgentMetadata(
            id="sales-agent",
            name="Sales Agent",
            description="Wide World Importers sales specialist. Analyzes customer relationships, sales performance, orders, invoices, and revenue opportunities.",
            system_prompt=load_prompt("sales_agent_prompt.txt"),
            model="gpt-4.1",
            temperature=0.5,
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
                "customer_management",
                "order_tracking",
                "revenue_analysis",
                "customer_insights"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 4. Warehouse Agent (ACTIVE - Wide World Importers)
        AgentMetadata(
            id="warehouse-agent",
            name="Warehouse Agent",
            description="Wide World Importers warehouse specialist. Manages inventory levels, stock movements, reorder points, and warehouse operations.",
            system_prompt=load_prompt("warehouse_agent_prompt.txt"),
            model="gpt-4.1",
            temperature=0.5,
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
                "inventory_management",
                "stock_tracking",
                "reorder_alerts",
                "warehouse_optimization",
                "stock_analysis"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 5. Purchasing Agent (ACTIVE - Wide World Importers)
        AgentMetadata(
            id="purchasing-agent",
            name="Purchasing Agent",
            description="Wide World Importers purchasing specialist. Manages suppliers, purchase orders, procurement efficiency, and vendor relationships.",
            system_prompt=load_prompt("purchasing_agent_prompt.txt"),
            model="gpt-4.1",
            temperature=0.5,
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
                "supplier_management",
                "purchase_order_tracking",
                "procurement_analysis",
                "vendor_performance",
                "cost_optimization"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 6. Customer Service Agent (ACTIVE - Wide World Importers)
        AgentMetadata(
            id="customer-service-agent",
            name="Customer Service Agent",
            description="Wide World Importers customer service specialist. First point of contact for customer inquiries, order tracking, and issue resolution.",
            system_prompt=load_prompt("customer_service_agent_prompt.txt"),
            model="gpt-4.1",
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
                "customer_support",
                "order_tracking",
                "issue_resolution",
                "cross_functional_queries",
                "customer_communication"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 7. Finance Agent (ACTIVE - Wide World Importers)
        AgentMetadata(
            id="finance-agent",
            name="Finance Agent",
            description="Wide World Importers finance specialist. Manages accounts receivable/payable, financial transactions, credit management, and financial reporting.",
            system_prompt=load_prompt("finance_agent_prompt.txt"),
            model="gpt-4.1",
            temperature=0.5,
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
                "financial_analysis",
                "accounts_receivable",
                "accounts_payable",
                "credit_management",
                "payment_tracking"
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
