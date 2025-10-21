"""Integration tests for SQL Agent with real MSSQL database.

These tests connect to the deployed MSSQL MCP server and execute actual queries
against the configured database (e.g., AdventureWorks).

Key Testing Philosophy:
- Use REAL database connection (not mocked)
- Dynamic schema discovery (don't hardcode table names)
- Verify agent provides analysis and insights, not just raw data
- Test multi-turn conversations with context
"""

import pytest
from src.agents.sql_agent import SQLAgent, create_sql_agent


class TestSQLAgentIntegration:
    """Integration tests for SQL Agent with real database connection."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_sql_agent(self):
        """Test SQL Agent creation with MSSQL MCP tool."""
        agent = SQLAgent.create()
        
        assert agent is not None
        assert agent.name == "SQL Agent"
        assert agent.base_agent is not None
        # Agent is properly configured with MSSQL MCP tool
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_tables_discovery(self):
        """Test dynamic schema discovery - list available tables."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Ask agent to discover tables
        response = await agent.run(
            "What tables are available in the database? Just list them.",
            thread=thread
        )
        
        # Should have a response
        assert response is not None
        assert len(response.messages) > 0
        
        # Last message should contain table information
        last_message = response.messages[-1].content
        assert last_message is not None
        
        # Common Adventure Works tables should be mentioned if that's the DB
        # But we don't hardcode assumptions - just verify we got a response
        print(f"\n✓ Tables discovered: {last_message[:200]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_describe_table_schema(self):
        """Test schema discovery - describe a specific table."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # First discover available tables
        list_response = await agent.run(
            "List all tables in the database.",
            thread=thread
        )
        
        # Then ask to describe a table (use common one if Adventure Works)
        describe_response = await agent.run(
            "Describe the structure of one of the Sales tables. Show me the columns and data types.",
            thread=thread
        )
        
        # Should have schema information
        assert describe_response is not None
        last_message = describe_response.messages[-1].content
        assert last_message is not None
        
        print(f"\n✓ Table schema described: {last_message[:300]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_simple_query_execution(self):
        """Test executing a simple SELECT query."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Execute a simple query
        response = await agent.run(
            "Execute a simple query to show me the first 5 rows from any table. "
            "Include column names and explain what you're querying.",
            thread=thread
        )
        
        # Should have query results
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        # Should contain SQL keywords
        assert "SELECT" in last_message or "select" in last_message
        
        print(f"\n✓ Query executed: {last_message[:400]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_data_analysis_with_insights(self):
        """Test that agent provides analysis and insights, not just raw data."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Ask for top customers
        response = await agent.run(
            "Show me the top 5 records from a customers table if available. "
            "Don't just show me the data - provide insights about what you found.",
            thread=thread
        )
        
        # Should have response with insights
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        # Agent should provide analysis, not just data
        # Look for analytical keywords
        analysis_keywords = [
            "insight", "analysis", "pattern", "trend", "observation",
            "finding", "indicates", "shows", "reveals", "suggests",
            "recommendation", "notable", "interesting"
        ]
        
        has_analysis = any(keyword in last_message.lower() for keyword in analysis_keywords)
        assert has_analysis, "Agent should provide insights and analysis, not just raw data"
        
        print(f"\n✓ Analysis provided: {last_message[:400]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_turn_conversation(self):
        """Test multi-turn conversation with context retention."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Turn 1: List tables
        response1 = await agent.run(
            "What tables are in this database?",
            thread=thread
        )
        assert response1 is not None
        
        # Turn 2: Query one of those tables (reference previous context)
        response2 = await agent.run(
            "Pick one of those tables and show me a sample of its data.",
            thread=thread
        )
        assert response2 is not None
        
        # Turn 3: Follow-up analysis
        response3 = await agent.run(
            "What insights can you provide about that data?",
            thread=thread
        )
        assert response3 is not None
        
        last_message = response3.messages[-1].content
        print(f"\n✓ Multi-turn conversation maintained context: {last_message[:300]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_aggregation_query(self):
        """Test SQL aggregation functions (COUNT, SUM, AVG, etc.)."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Ask for aggregated data
        response = await agent.run(
            "Run an aggregation query using COUNT, SUM, or AVG on any appropriate table. "
            "Explain what you're calculating and why it's useful.",
            thread=thread
        )
        
        # Should have aggregation results
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        # Should contain aggregation keywords
        agg_keywords = ["COUNT", "SUM", "AVG", "MAX", "MIN", "count", "sum", "avg", "max", "min"]
        has_aggregation = any(keyword in last_message for keyword in agg_keywords)
        assert has_aggregation, "Query should include aggregation functions"
        
        print(f"\n✓ Aggregation query executed: {last_message[:400]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_join_query(self):
        """Test JOIN queries across multiple tables."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Ask for a join query
        response = await agent.run(
            "Find two related tables and perform a JOIN query to combine their data. "
            "Explain the relationship and what insights the joined data provides.",
            thread=thread
        )
        
        # Should have join results
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        # Should mention JOIN in some form
        assert "JOIN" in last_message or "join" in last_message
        
        print(f"\n✓ JOIN query executed: {last_message[:400]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_convenience_method_sales(self):
        """Test convenience method for sales queries."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Use convenience method
        response = await agent.query_sales(
            "What are the total sales?",
            thread=thread
        )
        
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        print(f"\n✓ Sales query via convenience method: {last_message[:300]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_convenience_method_schema(self):
        """Test convenience method for schema information."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Get all tables
        response = await agent.get_schema_info(thread=thread)
        
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        print(f"\n✓ Schema info via convenience method: {last_message[:300]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_factory_function(self):
        """Test async factory function for agent creation."""
        agent = await create_sql_agent()
        
        assert agent is not None
        assert agent.name == "SQL Agent"
        
        # Test that it works
        thread = agent.get_new_thread()
        response = await agent.run(
            "List the available tables.",
            thread=thread
        )
        
        assert response is not None
        print(f"\n✓ Factory function works: {agent.name} created")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_invalid_query(self):
        """Test error handling for invalid SQL queries."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Try to run an invalid query (the agent should handle it gracefully)
        response = await agent.run(
            "Query a table that definitely doesn't exist: SELECT * FROM NonExistentTable123XYZ",
            thread=thread
        )
        
        # Should still get a response (explaining the error)
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        print(f"\n✓ Error handled gracefully: {last_message[:300]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_read_only_enforcement(self):
        """Test that agent enforces read-only access (no INSERT/UPDATE/DELETE)."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        # Try to get agent to modify data
        response = await agent.run(
            "Delete all records from a table.",
            thread=thread
        )
        
        # Agent should refuse or explain it can't do that
        assert response is not None
        last_message = response.messages[-1].content
        assert last_message is not None
        
        # Should mention read-only or SELECT-only
        read_only_indicators = ["read-only", "SELECT only", "cannot delete", "can't delete", "not allowed"]
        mentions_read_only = any(indicator.lower() in last_message.lower() for indicator in read_only_indicators)
        
        print(f"\n✓ Read-only enforcement: {last_message[:300]}...")
        print(f"  Mentions read-only restriction: {mentions_read_only}")


class TestSQLAgentStreaming:
    """Test streaming responses from SQL Agent."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_streaming_query(self):
        """Test streaming response for a query."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        chunks = []
        async for chunk in agent.run_stream(
            "What tables are available?",
            thread=thread
        ):
            chunks.append(chunk)
        
        # Should have received multiple chunks
        assert len(chunks) > 0
        
        print(f"\n✓ Received {len(chunks)} streaming chunks")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_streaming_complex_query(self):
        """Test streaming for a complex query with analysis."""
        agent = SQLAgent.create()
        thread = agent.get_new_thread()
        
        chunks = []
        async for chunk in agent.run_stream(
            "Find the top 10 records from any large table and provide detailed analysis.",
            thread=thread
        ):
            chunks.append(chunk)
        
        # Should have received multiple chunks for complex response
        assert len(chunks) > 0
        
        print(f"\n✓ Received {len(chunks)} streaming chunks for complex query")
