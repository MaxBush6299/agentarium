"""
Agent Seeding
Seeds default agents into Cosmos DB on application startup.

Default Agents:
1. Support Triage Agent - Active, with MCP + OpenAPI tools
2. Azure Ops Agent - Active, with MCP + OpenAPI tools
3. SQL Agent - Inactive, placeholder for future development
4. News Agent - Inactive, placeholder for future development
5. Business Impact Agent - Inactive, placeholder for future development
"""
import logging
from typing import List
from src.persistence.agents import get_agent_repository
from src.persistence.models import AgentMetadata, AgentStatus, ToolType, ToolConfig

logger = logging.getLogger(__name__)


def get_default_agents() -> List[AgentMetadata]:
    """
    Define default agents to seed into the database.
    
    Returns:
        List of AgentMetadata objects representing default agents
    """
    return [
        # 1. Support Triage Agent (ACTIVE)
        AgentMetadata(
            id="support-triage",
            name="Support Triage Agent",
            description="Helps triage and analyze customer support issues using Microsoft documentation and knowledge bases. Searches technical docs, suggests solutions, and identifies relevant articles.",
            system_prompt="""You are a specialized support triage agent. Your role is to help analyze customer support issues and provide initial guidance.

Your capabilities:
- Search Microsoft Learn documentation for relevant technical information
- Access knowledge bases and support articles
- Suggest troubleshooting steps and solutions
- Identify appropriate support escalation paths

When helping with an issue:
1. Ask clarifying questions to understand the problem
2. Search documentation for relevant information
3. Provide step-by-step troubleshooting guidance
4. Suggest appropriate resources or escalation if needed

Be concise, accurate, and helpful. Always cite your sources when referencing documentation.""",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4000,
            max_messages=20,
            tools=[
                ToolConfig(
                    type=ToolType.MCP,
                    name="microsoft-docs",
                    mcp_server_name="microsoft-learn-mcp",
                    config={"description": "Search Microsoft Learn documentation"},
                    enabled=True
                ),
                ToolConfig(
                    type=ToolType.OPENAPI,
                    name="support-triage-api",
                    openapi_spec_path="openapi/support-triage-api.yaml",
                    config={"description": "Support ticket management operations"},
                    enabled=True
                )
            ],
            capabilities=[
                "documentation_search",
                "issue_triage",
                "solution_suggestion",
                "troubleshooting_guidance"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 2. Azure Ops Agent (ACTIVE)
        AgentMetadata(
            id="azure-ops",
            name="Azure Operations Agent",
            description="Helps manage and troubleshoot Azure resources. Can query Azure resources, check deployment status, analyze logs, and provide operational insights.",
            system_prompt="""You are an Azure operations specialist agent. Your role is to help users manage and troubleshoot Azure resources.

Your capabilities:
- Query Azure resource information
- Check deployment and provisioning status
- Analyze Azure Monitor logs and metrics
- Search Azure documentation
- Suggest operational best practices

When helping with Azure operations:
1. Understand the Azure resources involved
2. Check current status and configuration
3. Search logs and metrics for issues
4. Provide actionable recommendations
5. Reference official Azure documentation

Be precise with Azure terminology and provide CLI/PowerShell commands when helpful.""",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4000,
            max_messages=20,
            tools=[
                ToolConfig(
                    type=ToolType.MCP,
                    name="microsoft-docs",
                    mcp_server_name="microsoft-learn-mcp",
                    config={"description": "Search Azure documentation"},
                    enabled=True
                ),
                ToolConfig(
                    type=ToolType.OPENAPI,
                    name="ops-assistant-api",
                    openapi_spec_path="openapi/ops-assistant-api.yaml",
                    config={"description": "Azure resource management operations"},
                    enabled=True
                )
            ],
            capabilities=[
                "azure_resource_query",
                "deployment_status",
                "log_analysis",
                "operational_insights",
                "documentation_search"
            ],
            status=AgentStatus.ACTIVE,
            is_public=True,
            version="1.0.0"
        ),
        
        # 3. SQL Agent (INACTIVE - Placeholder)
        AgentMetadata(
            id="sql-agent",
            name="SQL Query Agent",
            description="Helps write, optimize, and troubleshoot SQL queries. Placeholder for future development.",
            system_prompt="""You are a SQL specialist agent. Your role is to help users write, optimize, and troubleshoot SQL queries.

Your capabilities:
- Write SQL queries based on natural language descriptions
- Optimize existing queries for performance
- Explain query execution plans
- Suggest indexing strategies
- Identify common SQL anti-patterns

When helping with SQL:
1. Understand the data schema and requirements
2. Write clear, efficient SQL queries
3. Explain your reasoning and approach
4. Provide optimization suggestions when relevant

Be precise with SQL syntax and follow best practices.""",
            model="gpt-4o",
            temperature=0.5,
            max_tokens=4000,
            max_messages=20,
            tools=[],  # No tools configured yet
            capabilities=[
                "sql_generation",
                "query_optimization",
                "schema_analysis",
                "performance_tuning"
            ],
            status=AgentStatus.INACTIVE,
            is_public=True,
            version="0.1.0"
        ),
        
        # 4. News Agent (INACTIVE - Placeholder)
        AgentMetadata(
            id="news-agent",
            name="News Research Agent",
            description="Searches and summarizes news articles on specific topics. Placeholder for future development.",
            system_prompt="""You are a news research agent. Your role is to find, analyze, and summarize news articles on specific topics.

Your capabilities:
- Search news sources for relevant articles
- Summarize key points from multiple articles
- Identify trending topics and themes
- Provide context and background information

When researching news:
1. Search for recent, relevant articles
2. Verify sources and credibility
3. Summarize key points objectively
4. Highlight different perspectives when available

Be objective, cite your sources, and focus on factual reporting.""",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4000,
            max_messages=15,
            tools=[],  # No tools configured yet
            capabilities=[
                "news_search",
                "article_summarization",
                "trend_analysis",
                "source_verification"
            ],
            status=AgentStatus.INACTIVE,
            is_public=True,
            version="0.1.0"
        ),
        
        # 5. Business Impact Agent (INACTIVE - Placeholder)
        AgentMetadata(
            id="business-impact",
            name="Business Impact Analyzer",
            description="Analyzes the business impact of technical decisions and incidents. Placeholder for future development.",
            system_prompt="""You are a business impact analysis agent. Your role is to assess the business impact of technical decisions and incidents.

Your capabilities:
- Analyze incident severity and business impact
- Estimate downtime costs and user impact
- Provide prioritization recommendations
- Assess risk levels for technical changes

When analyzing business impact:
1. Gather information about the incident or decision
2. Identify affected services and users
3. Estimate business impact (revenue, reputation, etc.)
4. Provide prioritization and mitigation recommendations

Be analytical, data-driven, and focus on business outcomes.""",
            model="gpt-4o",
            temperature=0.6,
            max_tokens=3000,
            max_messages=15,
            tools=[],  # No tools configured yet
            capabilities=[
                "impact_analysis",
                "severity_assessment",
                "cost_estimation",
                "risk_analysis",
                "prioritization"
            ],
            status=AgentStatus.INACTIVE,
            is_public=True,
            version="0.1.0"
        ),
    ]


def seed_agents() -> dict:
    """
    Seed default agents into the database.
    
    This function is idempotent - it will only create agents that don't exist.
    Existing agents are not modified to preserve customizations.
    
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
    
    for agent in agents:
        try:
            # Check if agent already exists
            existing = repo.get(agent.id)
            
            if existing:
                logger.info(f"Agent already exists, skipping: {agent.id}")
                skipped += 1
            else:
                # Upsert new agent (create or update)
                repo.upsert(agent)
                logger.info(f"Upserted agent: {agent.id} ({agent.name}) - Status: {agent.status.value}")
                created += 1
                
        except Exception as e:
            logger.error(f"Failed to seed agent {agent.id}: {e}")
            # Continue with other agents
    
    result = {
        "created": created,
        "skipped": skipped,
        "total": len(agents)
    }
    
    logger.info(f"Agent seeding complete: {created} created, {skipped} skipped, {len(agents)} total")
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
