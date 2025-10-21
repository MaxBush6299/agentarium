"""SQL Agent Implementation - Database Analyst with Dynamic Tool Discovery.

This module implements the SQL Agent, which specializes in querying and
analyzing data from MSSQL databases using the MSSQL MCP tool.

The agent uses:
- MSSQL MCP tool with dynamic tool discovery
- GPT-4o model for intelligent SQL generation and data analysis
- Works with any MSSQL database configured in the MCP server
"""

import logging
from typing import Optional

from .base import DemoBaseAgent
from ..tools.mcp_tools import get_mssql_tool

logger = logging.getLogger(__name__)


# SQL Agent system prompt
SQL_AGENT_SYSTEM_PROMPT = """You are a data analyst and SQL expert with access to a MSSQL database through MCP tools.

**Your Primary Responsibilities:**
1. **Discover database schema** using available MCP tools
2. **Answer business questions** by generating and executing SQL queries
3. **Provide deep analysis** - don't just return raw data, extract insights and patterns
4. **Explain findings** in clear, business-friendly language
5. **Suggest actionable recommendations** based on data analysis

**Available MCP Tools:**

You have access to several tools for database operations. Use dynamic tool discovery to see all available tools, but typically you'll use:

- **list_tables**: Discover all tables in the database
- **describe_table**: Get detailed schema for a specific table (columns, types, constraints)
- **read_data**: Execute SELECT queries to retrieve and analyze data
- **Other tools**: Check for additional tools that might help with specific operations

**Workflow - Always Follow These Steps:**

1. **Schema Discovery (First Time):**
   - Use `list_tables` to see what tables exist
   - Use `describe_table` on relevant tables to understand their structure
   - Identify relationships between tables (foreign keys, common columns)

2. **Query Planning:**
   - Understand what the user is asking
   - Identify which tables and columns you need
   - Plan proper JOINs if multiple tables are involved
   - Consider filters (WHERE) and aggregations (GROUP BY)

3. **Query Execution:**
   - Write optimized SQL using `read_data`
   - Use proper syntax (TOP N, ORDER BY, etc.)
   - Keep queries read-only (SELECT only)

4. **Analysis & Insights (CRITICAL):**
   - Don't just show the raw data
   - Calculate percentages, trends, comparisons
   - Identify patterns, anomalies, or interesting findings
   - Explain what the numbers mean in business terms
   - Highlight top performers, outliers, or areas of concern

5. **Recommendations:**
   - Suggest actions based on the analysis
   - Propose follow-up questions for deeper insights
   - Connect findings to business value

**Query Guidelines:**

- **Read-Only**: Only SELECT statements (no INSERT, UPDATE, DELETE, DROP)
- **Proper JOINs**: Use INNER, LEFT, RIGHT joins appropriately
- **WHERE Clauses**: Filter data to avoid massive result sets
- **Aggregations**: Use SUM, COUNT, AVG, MIN, MAX with GROUP BY
- **Ordering**: ORDER BY relevant columns (DESC for top N)
- **Limits**: Use TOP N to keep results manageable
- **Performance**: Avoid overly complex queries; break into steps if needed

**Response Format - Follow This Template:**

1. **Understanding**: Confirm what you're analyzing
2. **Schema Check**: If first query or new tables, show what you discovered
3. **Approach**: Explain how you'll answer the question
4. **SQL Query**: Show the formatted query with comments
5. **Results**: Present data in clear table format
6. **Analysis & Insights**: 
   - What patterns do you see?
   - What are the key findings?
   - How do values compare (percentages, rankings)?
   - Are there any surprises or anomalies?
7. **Business Impact**: What does this mean for the business?
8. **Recommendations**: What actions or follow-ups make sense?

**Example Interaction:**

User: "What are our top 5 products by revenue?"

Your Response:
"I'll analyze product sales to identify the highest revenue generators.

**Step 1: Schema Discovery**
Let me first check the available tables...

[Use list_tables tool]

I can see Sales and Production tables. Let me examine the relevant ones:

[Use describe_table on Sales.SalesOrderDetail and Production.Product]

**Step 2: Query Approach**
I'll join SalesOrderDetail (which has line items and amounts) with Product (which has product names) to calculate total revenue per product.

**SQL Query:**
```sql
SELECT TOP 5
    p.Name AS ProductName,
    p.ProductNumber,
    SUM(sod.LineTotal) AS TotalRevenue,
    COUNT(DISTINCT sod.SalesOrderID) AS OrderCount,
    AVG(sod.LineTotal) AS AvgOrderValue
FROM Sales.SalesOrderDetail sod
INNER JOIN Production.Product p ON sod.ProductID = p.ProductID
GROUP BY p.Name, p.ProductNumber
ORDER BY TotalRevenue DESC
```

**Results:**
| ProductName | ProductNumber | TotalRevenue | OrderCount | AvgOrderValue |
|-------------|---------------|--------------|------------|---------------|
| Mountain-200 Black | BK-M68B-46 | $1,200,576.89 | 489 | $2,455.17 |
| Road-250 Red | BK-R93R-48 | $985,423.12 | 412 | $2,392.28 |
| ... | ... | ... | ... | ... |

**Analysis & Insights:**
- **Revenue Concentration**: The top 5 products generate $4.5M in revenue, representing 28% of total sales
- **Order Volume Leader**: Mountain-200 Black has the most orders (489), indicating strong market demand
- **Premium Positioning**: These products have avg order values above $2,300, suggesting premium market segment
- **Mountain vs Road**: 3 of top 5 are mountain bikes, indicating this category's importance

**Business Impact:**
- These 5 products are critical to revenue - any supply issues would significantly impact sales
- The high order volume for Mountain-200 Black suggests successful product-market fit
- Premium pricing strategy is working well for these products

**Recommendations:**
1. **Inventory Priority**: Ensure these products are always in stock
2. **Marketing Focus**: Allocate marketing budget to promote these proven winners
3. **Product Development**: Investigate what makes these products successful; consider expanding product line
4. **Regional Analysis**: Next, we should analyze which regions/territories drive sales for these products

**Suggested Follow-up Questions:**
- "Show me sales trends for these products over the last 12 months"
- "Which customer segments are buying these top products?"
- "How do these products perform across different sales territories?"
- "What's the profit margin on these high-revenue products?"

---

**Key Principles:**

- **Discovery First**: Always explore schema before writing queries
- **Context Matters**: Understand the business question, not just the data request
- **Insights Over Data**: Raw data is useful, but analysis creates value
- **Clear Communication**: Use formatting, tables, percentages, comparisons
- **Actionable Output**: Connect findings to decisions and recommendations
- **Tool Mastery**: Leverage all available MCP tools efficiently

Be thorough, analytical, and help users make data-driven decisions!"""


class SQLAgent:
    """
    SQL Agent for MSSQL database analysis with dynamic tool discovery.
    
    This agent specializes in:
    - Dynamic schema discovery
    - SQL query generation and execution
    - Deep data analysis with insights
    - Business intelligence reporting
    
    The agent works with any MSSQL database configured in the MCP server,
    using dynamic tool discovery to adapt to available operations.
    
    Attributes:
        base_agent (DemoBaseAgent): Underlying agent implementation
        name (str): Agent display name
        
    Example:
        ```python
        # Create agent
        agent = SQLAgent.create()
        
        # Get a new conversation thread
        thread = agent.get_new_thread()
        
        # Run agent with a query
        response = await agent.run(
            "What are the top 5 customers by total sales?",
            thread=thread
        )
        print(response.messages[-1].content)
        
        # Follow-up question with context
        response = await agent.run(
            "Show me their order history from last year",
            thread=thread
        )
        ```
    """
    
    def __init__(self, base_agent: DemoBaseAgent):
        """
        Initialize SQL Agent with a base agent.
        
        Args:
            base_agent: Configured DemoBaseAgent instance with MSSQL MCP tool
        """
        self.base_agent = base_agent
        self.name = "SQL Agent"
        logger.info(f"Initialized {self.name}")
    
    @classmethod
    def create(
        cls,
        model: str = "gpt-4o",
        max_messages: int = 20,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> "SQLAgent":
        """
        Create a new SQL Agent with default configuration.
        
        This factory method creates a fully configured agent with:
        - MSSQL MCP tool with dynamic tool discovery
        - Optimized system prompt for SQL and data analysis
        - Sliding window memory (20 messages default)
        - SQL query validation and safety
        
        Args:
            model: Azure OpenAI model deployment name (default: "gpt-4o")
            max_messages: Maximum messages in sliding window (default: 20)
            temperature: Model temperature for response generation (default: 0.7)
            max_tokens: Maximum tokens per response (default: None)
            
        Returns:
            SQLAgent: Configured agent instance
            
        Raises:
            ValueError: If agent creation fails
            ConnectionError: If MSSQL MCP tool cannot be initialized
            
        Example:
            ```python
            # Create with defaults
            agent = SQLAgent.create()
            
            # Create with custom configuration
            agent = SQLAgent.create(
                model="gpt-4",
                max_messages=30,
                temperature=0.5
            )
            ```
        """
        logger.info("Creating SQL Agent")
        
        # Create MSSQL MCP tool with dynamic discovery
        try:
            mssql_tool = get_mssql_tool()
            logger.info("MSSQL MCP tool initialized with dynamic discovery")
        except Exception as e:
            error_msg = f"Failed to initialize MSSQL MCP tool: {e}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        
        # Create base agent with tool
        base_agent = DemoBaseAgent(
            name="SQL Agent",
            instructions=SQL_AGENT_SYSTEM_PROMPT,
            tools=[mssql_tool],
            model=model,
            max_messages=max_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        logger.info(f"SQL Agent created with model={model}")
        
        # Wrap in SQLAgent
        return cls(base_agent)
    
    # Delegate core methods to base_agent
    
    async def run(self, *args, **kwargs):
        """Run the agent. Delegates to base_agent.run()."""
        return await self.base_agent.run(*args, **kwargs)
    
    async def run_stream(self, *args, **kwargs):
        """Stream agent responses. Delegates to base_agent.run_stream()."""
        async for update in self.base_agent.run_stream(*args, **kwargs):
            yield update
    
    def get_new_thread(self, **kwargs):
        """Create a new conversation thread. Delegates to base_agent."""
        return self.base_agent.get_new_thread(**kwargs)
    
    # Convenience methods for common SQL operations
    
    async def query_sales(
        self,
        question: str,
        thread=None
    ):
        """
        Convenience method for sales-related queries.
        
        Args:
            question: Business question about sales data
            thread: Optional conversation thread
            
        Returns:
            Agent response with SQL query and results
        """
        enhanced_question = f"[Sales Analysis] {question}"
        return await self.run(enhanced_question, thread=thread)
    
    async def query_customers(
        self,
        question: str,
        thread=None
    ):
        """
        Convenience method for customer-related queries.
        
        Args:
            question: Business question about customer data
            thread: Optional conversation thread
            
        Returns:
            Agent response with SQL query and results
        """
        enhanced_question = f"[Customer Analysis] {question}"
        return await self.run(enhanced_question, thread=thread)
    
    async def query_products(
        self,
        question: str,
        thread=None
    ):
        """
        Convenience method for product-related queries.
        
        Args:
            question: Business question about product data
            thread: Optional conversation thread
            
        Returns:
            Agent response with SQL query and results
        """
        enhanced_question = f"[Product Analysis] {question}"
        return await self.run(enhanced_question, thread=thread)
    
    async def get_schema_info(
        self,
        table_name: Optional[str] = None,
        thread=None
    ):
        """
        Get database schema information.
        
        Args:
            table_name: Specific table to describe (None for all tables)
            thread: Optional conversation thread
            
        Returns:
            Agent response with schema details
        """
        if table_name:
            question = f"Describe the structure and columns of the {table_name} table"
        else:
            question = "List all available tables in the database with their purposes"
        
        return await self.run(question, thread=thread)


# Factory function for consistency with other agents
async def create_sql_agent(
    model: str = "gpt-4o",
    max_messages: int = 20,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> SQLAgent:
    """
    Async factory function to create a SQL Agent.
    
    This is an async wrapper around SQLAgent.create() for consistency
    with other agent creation patterns.
    
    Args:
        model: Azure OpenAI model deployment name (default: "gpt-4o")
        max_messages: Maximum messages in sliding window (default: 20)
        temperature: Model temperature for response generation (default: 0.7)
        max_tokens: Maximum tokens per response (default: None)
        
    Returns:
        SQLAgent: Configured agent instance
        
    Example:
        ```python
        # Create SQL agent
        agent = await create_sql_agent()
        
        # Query sales data with dynamic tool discovery
        response = await agent.run("What are the available tables?")
        response = await agent.run("What are the top 10 customers by total sales?")
        ```
    """
    return SQLAgent.create(
        model=model,
        max_messages=max_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
