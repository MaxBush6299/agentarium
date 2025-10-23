# Router Agent Architecture - Visual Guide

## Quick Reference

### The Chain: How It Works

```
User asks: "Show me Q4 sales trends and create a dashboard"
                            ↓
                   Router Agent receives query
                            ↓
        "This needs data + analysis. I'll:"
        "1. Get data from SQL Agent
         2. Send to Analytics Agent"
                            ↓
                ┌───────────┴──────────────┐
                ↓                          ↓
          SQL Agent                  Analytics Agent
          (via A2A)                  (via A2A)
            Query data               Create report
          Returns: [sales data]      Returns: [dashboard]
                ↓                          ↓
                └───────────┬──────────────┘
                            ↓
                    Router synthesizes results
                            ↓
                    Returns to user:
                  "Q4 Sales Dashboard"
                  [Data + Report]
```

---

## Agent Specialization

```
┌─────────────────────────────────────────────────────────────┐
│                        ROUTER AGENT                          │
│  (Intelligent Dispatcher - Understands Intent)              │
└────────────┬──────────────┬──────────────┬─────────────────┘
             │              │              │
      ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
      │  SQL Agent  │ │  Support  │ │ Azure Ops  │  ← ← ← →
      │   (Data)    │ │  Triage   │ │ (Infra)    │
      │             │ │  (Docs)   │ │            │
      └─────────────┘ └───────────┘ └────────────┘
                              ↑
                              │
                    ┌─────────▼────────┐
                    │ Data Analytics   │
                    │ (Intelligence)   │
                    └──────────────────┘
```

**Router's Job:**
- Listen to user query
- Understand what they're asking
- Pick the right specialist(s)
- Call via A2A protocol
- Return results

---

## Routing Decision Map

```
User Query Classification:

┌─ "Show me data from Adventure Works" 
│  → SQL Agent
│     └─ Tables, sales, customers, orders
│
├─ "Create a dashboard" / "Analyze trends"
│  → Data Analytics Agent
│     └─ Insights, reports, visualizations
│
├─ "What's happening with my deployment?"
│  → Azure Ops Agent
│     └─ Infrastructure, monitoring, logs
│
├─ "How do I create an X?" / "Help me fix Y"
│  → Support Triage Agent
│     └─ Documentation, troubleshooting, guidance
│
└─ Complex queries (e.g., "Get sales data AND create report")
   → Multiple agents in sequence
      └─ SQL → Analytics, or SQL + Ops + Analytics
```

---

## Tool Configuration

### A2A Tools in Router Agent

Each specialist is configured as an A2A tool:

```
┌─ A2A Tool: "sql-agent"
│  └─ Calls agent_id: "sql-agent"
│
├─ A2A Tool: "azure-ops"
│  └─ Calls agent_id: "azure-ops"
│
├─ A2A Tool: "support-triage"
│  └─ Calls agent_id: "support-triage"
│
└─ A2A Tool: "data-analytics"
   └─ Calls agent_id: "data-analytics"
```

**Tool Type:** A2A Protocol (standardized agent-to-agent)  
**Invocation:** Agent calls tool → triggers specialist agent  
**Result:** Specialist's response returned to Router  

---

## Data Flow Timeline

```
T0: User sends message to Router
    "Show me Q4 sales by region"

T1: Router receives message
    - Analyzes query
    - Decides to use SQL Agent

T2: Router calls SQL Agent via A2A tool
    - Parameters: Query about Q4 sales
    - A2A Protocol handles transport

T3: SQL Agent executes
    - Queries Adventure Works database
    - Formats results

T4: SQL Agent returns results
    - Via A2A protocol to Router

T5: Router receives results
    - Data available

T6: Router sends response to user
    - "Here's Q4 sales by region: [data]"
```

---

## Comparison: Before vs After

### BEFORE (No Router)
```
User
  ├─ "I need database help" → SQL Agent (manual)
  ├─ "I need infrastructure help" → Azure Ops (manual)
  └─ "I need support" → Support Triage (manual)

Problem: User must know which agent to use
```

### AFTER (With Router)
```
User
  └─ "I need sales trends" → Router Agent
      └─ Router intelligently routes to SQL + Analytics
         └─ Orchestrates multiple agents automatically
         
Benefit: User just asks naturally!
```

---

## Capabilities Summary

**Router Agent Capabilities:**
- ✅ intelligent_routing
- ✅ multi_agent_orchestration  
- ✅ request_delegation
- ✅ clarification (asks questions if unclear)
- ✅ composite_queries (chains multiple agents)

---

## Integration Points

### With Frontend
```
Frontend → API → Router Agent
                 ├─ SQL Agent
                 ├─ Azure Ops Agent
                 ├─ Support Triage Agent
                 └─ Data Analytics Agent
```

### With A2A Protocol
```
Router Agent uses A2A tools
├─ Each specialist has A2A agent card
├─ Router discovers via agent cards
└─ Calls via standardized A2A protocol
```

### With Tool Registry
```
Agent Factory creates Router Agent
    ├─ Loads 4 A2A tools from ToolRegistry
    ├─ Each tool points to specialist agent
    └─ All tools available for use
```

---

## Example Scenarios

### Scenario 1: Data Query
```
User: "What are the top 3 products by sales?"

Router: "This is a database query. I'll call SQL Agent."
  ↓
SQL Agent: Queries Adventure Works
  ↓
Router: "Top 3 products are..."
```

### Scenario 2: Composite Query
```
User: "Show me sales trends for Q1-Q4 and create a chart"

Router: "This needs data AND analytics. Calling both."
  ↓
SQL Agent: Gets quarterly sales data
  ↓
Data Analytics Agent: Creates chart from data
  ↓
Router: Returns chart + analysis
```

### Scenario 3: Help Needed
```
User: "How do I query a database?"

Router: "This is a documentation request. I'll call Support Triage."
  ↓
Support Triage: Searches documentation, returns guide
  ↓
Router: Returns help + examples
```

### Scenario 4: Clarification
```
User: "I need help"

Router: "I can help with many things. Are you asking about:
         - Data queries (SQL)?
         - Azure infrastructure?
         - Documentation/troubleshooting?
         - Business analytics?"

User: "Azure infrastructure"

Router: Calls Azure Ops Agent
```

---

## Success Metrics

### System Working Well If:
✅ Router correctly identifies specialist needed  
✅ A2A calls execute without errors  
✅ Results returned in reasonable time  
✅ Complex queries handled end-to-end  
✅ Each specialist operates independently  

### Areas to Monitor:
🔍 Routing accuracy (% of correct specialist chosen)  
🔍 A2A success rate (% of calls that succeed)  
🔍 End-to-end latency (time from user → response)  
🔍 Error handling (what happens when specialist fails)  

---

## Next Steps

1. **Test locally**
   - Start backend
   - Verify Router Agent loads
   - Call with test queries

2. **Verify A2A loading**
   - Check ToolRegistry creates A2A tools
   - Confirm specialist agents found

3. **End-to-end test**
   - Simple routing (Router → SQL)
   - Complex routing (Router → SQL → Analytics)
   - Error cases (specialist not available)

4. **Iterate**
   - Refine routing logic
   - Add more examples to system prompt
   - Optimize for latency

---

**Architecture Status:** ✅ Ready for Testing
