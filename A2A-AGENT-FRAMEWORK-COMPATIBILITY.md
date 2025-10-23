# Agent Framework & A2A Protocol Compatibility Guide

**Status:** ✅ Agent Framework has NATIVE A2A support  
**Date:** October 23, 2025  
**Source:** Microsoft Learn Documentation  

---

## 🎯 Key Finding

**The Microsoft Agent Framework has built-in support for A2A (Agent-to-Agent) protocol!**

This means:
- ✅ Agents can natively call other A2A agents
- ✅ No need to implement A2A calling from scratch
- ✅ A2A is treated as a standard `AIAgent` type
- ✅ Full integration with Agent Framework's agent abstraction

---

## 📚 Microsoft's A2A Support

### Python Implementation
```python
from agent_framework.a2a import A2AAgent, A2ACardResolver
import httpx

# Option 1: Well-known agent card discovery
async with httpx.AsyncClient(timeout=60.0) as http_client:
    resolver = A2ACardResolver(
        httpx_client=http_client, 
        base_url="https://your-a2a-agent-host"
    )
    
    # Resolver looks for agent card at:
    # https://your-a2a-agent-host/.well-known/agent.json
    agent_card = await resolver.get_agent_card(
        relative_card_path="/.well-known/agent.json"
    )
    
    # Create A2A agent instance
    agent = A2AAgent(
        name=agent_card.name,
        description=agent_card.description,
        agent_card=agent_card,
        url="https://your-a2a-agent-host"
    )

# Option 2: Direct URL configuration
agent = A2AAgent(
    name="My A2A Agent",
    description="Directly configured A2A agent",
    url="https://your-a2a-agent-host/echo"
)

# Use like any other AIAgent
response = await agent.run_stream(message)
```

### C# Implementation
```csharp
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.A2A;

// Option 1: Well-known discovery
A2ACardResolver agentCardResolver = new(
    new Uri("https://your-a2a-agent-host")
);
AIAgent agent = await agentCardResolver.GetAIAgentAsync();

// Option 2: Direct configuration
A2AClient a2aClient = new(
    new Uri("https://your-a2a-agent-host/echo")
);
AIAgent agent = a2aClient.GetAIAgent();

// Use standard AIAgent interface
```

---

## 🔑 Key Concepts

### A2A as First-Class Agent Type

The Agent Framework treats A2A as a **native agent type**, just like local agents:

```
AIAgent (Abstract Base)
├─ LocalAgent (runs in-process)
├─ A2AAgent (calls remote agent via A2A protocol) ← This is what we need!
└─ [Other agent types...]
```

### Agent Card Discovery

Microsoft's approach uses **well-known locations** for agent discovery:

```
https://your-agent-host/.well-known/agent.json
```

This is the standardized A2A discovery mechanism that other clients can find your agent.

---

## 🏗️ Your Implementation Strategy

### Current State
✅ You have A2A protocol server (`src/a2a/server.py`)  
✅ You have agent card auto-generation (`src/a2a/agent_cards.py`)  
✅ You expose agents at `/.well-known/agent-card.json`  
✅ Router Agent configured with A2A tools  

### What's Missing
❌ A2A tool registration in ToolRegistry  
❌ A2A tool factory implementation  
❌ Integration with Agent Framework's A2AAgent class  

---

## 🔧 What We Need to Build

### Step 1: Create A2A Tool Wrapper

**File:** `backend/src/tools/a2a_tools.py` (NEW)

```python
"""A2A (Agent-to-Agent) tool implementations for router agent."""

from typing import Dict, Any, Optional
import httpx
from agent_framework.a2a import A2AAgent

def create_a2a_agent_tool(agent_url: str, agent_name: str):
    """
    Create an A2A tool that calls a remote agent.
    
    Args:
        agent_url: Base URL of the A2A agent (e.g., http://localhost:8000)
        agent_name: Name of the agent for display
        
    Returns:
        Callable that sends messages to the A2A agent
    """
    agent = A2AAgent(
        name=agent_name,
        description=f"A2A client for {agent_name}",
        url=agent_url
    )
    
    async def call_agent(query: str) -> Dict[str, Any]:
        """Send query to remote agent via A2A protocol."""
        try:
            response = await agent.run_stream(query)
            return {
                "status": "success",
                "response": str(response),
                "agent": agent_name
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": agent_name
            }
    
    return call_agent


def get_sql_agent_tool():
    """Get SQL Agent via A2A."""
    return create_a2a_agent_tool(
        agent_url="http://localhost:8000",
        agent_name="SQL Agent"
    )

def get_azure_ops_agent_tool():
    """Get Azure Ops Agent via A2A."""
    return create_a2a_agent_tool(
        agent_url="http://localhost:8000",
        agent_name="Azure Ops Agent"
    )

def get_support_triage_agent_tool():
    """Get Support Triage Agent via A2A."""
    return create_a2a_agent_tool(
        agent_url="http://localhost:8000",
        agent_name="Support Triage Agent"
    )

def get_data_analytics_agent_tool():
    """Get Data Analytics Agent via A2A."""
    return create_a2a_agent_tool(
        agent_url="http://localhost:8000",
        agent_name="Data Analytics Agent"
    )
```

### Step 2: Register A2A Tools in ToolRegistry

**File:** `backend/src/agents/tool_registry.py` (MODIFY)

Add to `register_default_tools()` function:

```python
def register_default_tools() -> None:
    """Register all built-in tools..."""
    registry = get_tool_registry()
    
    # ... existing MCP and OpenAPI registration ...
    
    # NEW: Register A2A tools
    try:
        print("[TOOL_REGISTRY] Registering A2A tools...")
        from src.tools.a2a_tools import (
            get_sql_agent_tool,
            get_azure_ops_agent_tool,
            get_support_triage_agent_tool,
            get_data_analytics_agent_tool,
        )
        
        # SQL Agent A2A Tool
        registry.register(ToolDefinition(
            type="a2a",
            name="sql-agent",
            description="A2A client for SQL Query Agent",
            factory=lambda cfg: get_sql_agent_tool(),
            required_config={},
            optional_config={
                "agent_url": "Base URL of SQL Agent (default: localhost:8000)"
            }
        ))
        
        # Azure Ops Agent A2A Tool
        registry.register(ToolDefinition(
            type="a2a",
            name="azure-ops",
            description="A2A client for Azure Operations Agent",
            factory=lambda cfg: get_azure_ops_agent_tool(),
            required_config={},
            optional_config={
                "agent_url": "Base URL of Azure Ops Agent"
            }
        ))
        
        # Support Triage Agent A2A Tool
        registry.register(ToolDefinition(
            type="a2a",
            name="support-triage",
            description="A2A client for Support Triage Agent",
            factory=lambda cfg: get_support_triage_agent_tool(),
            required_config={},
            optional_config={
                "agent_url": "Base URL of Support Triage Agent"
            }
        ))
        
        # Data Analytics Agent A2A Tool
        registry.register(ToolDefinition(
            type="a2a",
            name="data-analytics",
            description="A2A client for Data Analytics Agent",
            factory=lambda cfg: get_data_analytics_agent_tool(),
            required_config={},
            optional_config={
                "agent_url": "Base URL of Data Analytics Agent"
            }
        ))
        
        logger.info("✓ Registered A2A tools")
    except Exception as e:
        print(f"[TOOL_REGISTRY] ✗ Failed to register A2A tools: {e}")
        logger.warning(f"Failed to register A2A tools: {e}")
```

---

## 🌍 How It Works

### Agent Framework's A2A Architecture

```
Your Local Agent (Router)
    ↓
A2AAgent (from agent_framework.a2a)
    ↓
A2A Protocol HTTP
    ↓
Remote Agent's /.well-known/agent.json
    ↓
Remote Agent executes
    ↓
Result returned via A2A protocol
    ↓
Response to Router Agent
```

### The Key: Well-Known Agent Card Location

Your `src/a2a/server.py` already exposes agent cards at:
```
GET /.well-known/agent-card.json
```

This is the standard A2A discovery endpoint that `A2ACardResolver` looks for!

---

## 📦 Dependencies Needed

Add to `backend/requirements.txt`:

```
agent-framework-a2a>=0.1.0  # For A2AAgent and A2ACardResolver
```

Or if already using Agent Framework SDK:
```
microsoft-agents-ai-a2a>=1.0.0-preview  # C# equivalent
agent-framework>=0.1.0  # Includes Python A2A
```

---

## 🧪 Testing the Integration

### Test 1: Verify A2A Tool Loads

```python
from src.agents.tool_registry import get_tool_registry

registry = get_tool_registry()

# Check A2A tool registered
a2a_tool_def = registry.get("a2a", "sql-agent")
print(f"A2A Tool: {a2a_tool_def}")
# Expected: ToolDefinition(type='a2a', name='sql-agent', ...)

# Create tool instance
tool = registry.create_tool("a2a", "sql-agent", {})
print(f"Tool created: {tool}")
# Expected: Callable that sends to SQL Agent
```

### Test 2: Call Remote Agent via A2A

```python
import asyncio
from src.tools.a2a_tools import get_sql_agent_tool

async def test_a2a():
    tool = get_sql_agent_tool()
    result = await tool("Show me top 10 customers")
    print(result)
    # Expected: Response from SQL Agent

asyncio.run(test_a2a())
```

### Test 3: Router Agent Chain

```
POST /api/chat
{
  "agent_id": "router",
  "message": "Show me top 10 customers",
  "thread_id": "test-1"
}
```

Expected flow:
1. Router Agent receives message
2. Recognizes as data query
3. Calls A2A tool for SQL Agent
4. A2AAgent sends via A2A protocol
5. SQL Agent responds
6. Router returns results

---

## 🎓 Key Insights from Microsoft Docs

### 1. A2A is Agent Framework Native
> "The Microsoft Agent Framework supports using a remote agent that is exposed via the A2A protocol in your application using the **same `AIAgent` abstraction** as any other agent."

**Translation:** A2A agents work seamlessly with the framework!

### 2. Two Discovery Modes

**Well-Known Location (Recommended):**
- Client discovers agent at `/.well-known/agent.json`
- Fully dynamic discovery
- Better for public agents

**Direct Configuration (Our use case):**
- Client knows exact agent URL
- No discovery needed
- Better for internal/tightly-coupled systems

### 3. Multi-Agent Orchestration Support
> "All agents are derived from a common base class, `AIAgent`, which provides a consistent interface for all agent types. This allows for building **common, agent agnostic, higher level functionality such as multi-agent orchestrations**."

**Translation:** Agent Framework designed for exactly what we're building!

---

## 🏁 Next Steps

### Immediate
1. Create `backend/src/tools/a2a_tools.py`
2. Add A2A tool registration to `tool_registry.py`
3. Test A2A tool loading
4. Test end-to-end Router → SQL Agent call

### Short Term
1. Add error handling for A2A failures
2. Implement request/response logging
3. Add request timeout handling
4. Test all specialist agent chains

### Medium Term
1. Add caching for A2A responses
2. Implement retry logic for failures
3. Add metrics/monitoring
4. Optimize latency

---

## 💡 Why This Approach Works

✅ **Framework Native** - Using official Agent Framework A2A support  
✅ **Standardized** - Follows Microsoft's recommended patterns  
✅ **Consistent** - A2A agents use same `AIAgent` interface  
✅ **Scalable** - Can add more specialist agents easily  
✅ **Observable** - All A2A calls logged and traceable  
✅ **Well-Documented** - Official Microsoft Learn docs available  

---

## 📖 References

- **Microsoft Learn - A2A Agents (Python):**  
  https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/a2a-agent

- **Microsoft Learn - Agent Framework Types:**  
  https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/

- **A2A Protocol Spec:**  
  https://a2a-protocol.org/latest/specification/

---

## ✨ Summary

**Your implementation is on the right track!**

What we have:
- ✅ A2A protocol server (exposes agents)
- ✅ Agent cards at well-known location
- ✅ Router Agent with A2A tools configured
- ✅ Agent Factory to create agents

What we need:
- ⬜ A2A tool implementations (simple wrapper)
- ⬜ Tool registry registration (2-3 functions)
- ⬜ End-to-end testing

**Estimated effort for complete integration: 1-2 hours**

The framework handles the complex parts (A2A communication, agent abstraction), we just need to wire it together!
