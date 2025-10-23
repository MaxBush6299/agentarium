# Router Agent Testing Guide

## Quick Start Testing

### Prerequisites
- Backend running (`python -m uvicorn src.main:app --reload`)
- Cosmos DB (local emulator or cloud)
- Agents seeded into database

---

## Test Cases

### Test 1: Verify Router Agent Exists

**Command:**
```bash
curl http://localhost:8000/api/agents/router
```

**Expected Response:**
```json
{
  "id": "router",
  "name": "Router Agent",
  "status": "active",
  "tools": [
    {"name": "sql-agent", "type": "a2a"},
    {"name": "azure-ops", "type": "a2a"},
    {"name": "support-triage", "type": "a2a"},
    {"name": "data-analytics", "type": "a2a"}
  ]
}
```

---

### Test 2: Simple Data Query (Router → SQL Agent)

**Query to send:**
```
"Show me the top 5 customers by total purchase amount from Adventure Works"
```

**Expected Routing:**
```
Router Agent (receives query)
  ↓
Identifies: "This is a database query"
  ↓
Calls SQL Agent via A2A tool
  ↓
SQL Agent queries Adventure Works
  ↓
Returns customer data
  ↓
Router returns results to user
```

**Success Criteria:**
- ✅ Router recognizes it as data query
- ✅ A2A call to SQL Agent succeeds
- ✅ Customer data returned
- ✅ Response includes SQL Agent's query logic

**API Call:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "router",
    "message": "Show me the top 5 customers by total purchase amount from Adventure Works",
    "thread_id": "test-thread-1"
  }'
```

---

### Test 3: Documentation Query (Router → Support Triage)

**Query to send:**
```
"How do I create an Azure storage account?"
```

**Expected Routing:**
```
Router Agent (receives query)
  ↓
Identifies: "This is a documentation/help request"
  ↓
Calls Support Triage Agent via A2A tool
  ↓
Support Triage searches Microsoft Learn
  ↓
Returns documentation + guide
  ↓
Router returns help text to user
```

**Success Criteria:**
- ✅ Router recognizes it as help request
- ✅ A2A call to Support Triage succeeds
- ✅ Documentation returned
- ✅ Response includes step-by-step guidance

**API Call:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "router",
    "message": "How do I create an Azure storage account?",
    "thread_id": "test-thread-2"
  }'
```

---

### Test 4: Infrastructure Query (Router → Azure Ops)

**Query to send:**
```
"What Azure resources do I have in my subscription?"
```

**Expected Routing:**
```
Router Agent (receives query)
  ↓
Identifies: "This is an Azure infrastructure question"
  ↓
Calls Azure Ops Agent via A2A tool
  ↓
Azure Ops queries Azure resources
  ↓
Returns resource list
  ↓
Router returns inventory to user
```

**Success Criteria:**
- ✅ Router recognizes it as infrastructure query
- ✅ A2A call to Azure Ops succeeds
- ✅ Azure resource list returned
- ✅ Response includes resource details

**API Call:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "router",
    "message": "What Azure resources do I have in my subscription?",
    "thread_id": "test-thread-3"
  }'
```

---

### Test 5: Composite Query (Router → SQL + Analytics)

**Query to send:**
```
"Show me Q1 and Q4 sales comparison and create a trend analysis"
```

**Expected Routing:**
```
Router Agent (receives query)
  ↓
Identifies: "Complex query - needs data + analysis"
  ↓
Calls SQL Agent via A2A tool
  ↓
SQL Agent returns Q1/Q4 sales data
  ↓
Calls Data Analytics Agent via A2A tool
  ↓
Analytics Agent creates trend analysis
  ↓
Router synthesizes both results
  ↓
Returns comparison + analysis
```

**Success Criteria:**
- ✅ Router recognizes as composite query
- ✅ First A2A call (SQL Agent) succeeds
- ✅ Second A2A call (Analytics Agent) succeeds
- ✅ Results combined intelligently
- ✅ Response includes data + analysis

**API Call:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "router",
    "message": "Show me Q1 and Q4 sales comparison and create a trend analysis",
    "thread_id": "test-thread-4"
  }'
```

---

### Test 6: Ambiguous Query (Router asks for clarification)

**Query to send:**
```
"I need help"
```

**Expected Behavior:**
```
Router Agent (receives query)
  ↓
Analyzes: "Too vague - multiple possibilities"
  ↓
Asks clarifying question:
"I can help with several things. Are you asking about:
 1. Data queries (SQL)?
 2. Azure infrastructure?
 3. Documentation/troubleshooting?
 4. Business analytics/reports?"
  ↓
Waits for user to clarify
```

**Success Criteria:**
- ✅ Router recognizes ambiguity
- ✅ Asks clarifying question
- ✅ Doesn't route prematurely
- ✅ Response guides user to right specialist

**API Call:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "router",
    "message": "I need help",
    "thread_id": "test-thread-5"
  }'
```

---

## Debugging Checklist

### If Test Fails: Check These

**1. Agent Loading**
```python
# Verify Router Agent created
python -c "
from src.persistence.agents import get_agent_repository
repo = get_agent_repository()
router = repo.get('router')
print(f'Router Agent: {router}')
print(f'Tools: {[t.name for t in router.tools]}')
"
```

**2. A2A Tool Registration**
```python
# Check ToolRegistry loads A2A tools
from src.agents.tool_registry import get_tool_registry
registry = get_tool_registry()
a2a_tool = registry.create_tool('a2a', 'sql-agent')
print(f'A2A Tool created: {a2a_tool}')
```

**3. Agent Factory**
```python
# Verify factory creates Router Agent with tools
from src.agents.factory import AgentFactory
from src.persistence.agents import get_agent_repository

repo = get_agent_repository()
router_metadata = repo.get('router')
agent = AgentFactory.create_from_metadata(router_metadata)
print(f'Agent: {agent.name}')
print(f'Tools available: {len(agent.tools)}')
```

**4. API Response**
```bash
# Check full API response
curl -v http://localhost:8000/api/agents/router

# Watch for:
# - 200 OK status
# - Proper agent metadata
# - All 4 A2A tools present
```

---

## Common Issues & Fixes

### Issue 1: Router Agent Not Found
```
Error: Agent 'router' not found
```

**Fix:**
1. Verify seed_agents.py updated (check line 29-90)
2. Restart backend (seeds run on startup)
3. Check database: `db.agents.find({"id": "router"})`

---

### Issue 2: A2A Tools Not Loading
```
Error: Tool 'sql-agent' failed to load
```

**Fix:**
1. Check ToolRegistry handles A2A type
2. Verify specialist agents exist in DB
3. Check tool_registry.py for A2A support
4. Look for error logs: `grep -i "a2a" backend.log`

---

### Issue 3: A2A Call Fails
```
Error: Failed to call specialist agent
```

**Fix:**
1. Verify specialist agent is ACTIVE (not INACTIVE)
2. Check specialist has no tools errors
3. Monitor backend logs during call
4. Test specialist directly first

---

### Issue 4: Timeout on Composite Query
```
Error: Request timeout after 30s
```

**Possible Causes:**
- Specialist agent slow
- Database query slow
- Too many messages in conversation

**Fix:**
- Increase timeout in settings
- Optimize specialist agent
- Clean up old threads

---

## Manual Testing Workflow

### Step 1: Start Backend
```bash
cd backend
python -m uvicorn src.main:app --reload
# Watch logs for: "Application startup complete"
```

### Step 2: Seed Database (if needed)
```bash
# If backend doesn't auto-seed, run:
python -c "
from src.persistence.seed_agents import seed_agents
stats = seed_agents()
print(stats)
"
```

### Step 3: Test Simple Query
```bash
# Easiest test to verify routing works
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "router",
    "message": "List the sales tables in Adventure Works",
    "thread_id": "quick-test"
  }'
```

### Step 4: Monitor Logs
```bash
# Watch backend logs for routing decisions
tail -f backend.log | grep -i "router\|a2a\|tool"
```

### Step 5: Verify Response
- ✅ Response received without error
- ✅ Response mentions specialist agent called
- ✅ Results make sense for query
- ✅ No timeout errors

---

## Performance Testing

### Latency Measurement

**Single Agent Call:**
```
Expected: 2-5 seconds
- Router decision: 100-300ms
- A2A protocol: 100-200ms
- Specialist execution: 1-3s
- Response synthesis: 200-500ms
Total: ~2-5s
```

**Composite Query:**
```
Expected: 4-10 seconds
- Router decision: 200ms
- First specialist: 2-3s
- Second specialist: 2-3s
- Synthesis: 500ms
Total: ~4-10s
```

---

## Success Indicators

### Router Working Correctly When:
✅ All 4 A2A tools load without errors  
✅ Simple queries route to correct specialist  
✅ Composite queries call multiple agents  
✅ Ambiguous queries ask for clarification  
✅ A2A calls complete successfully  
✅ Results returned in <5 seconds  
✅ No exceptions in logs  

---

## Test Summary Template

```
Date: [Date]
Tester: [Name]

Test 1: Verify Agent Exists
  Status: [PASS/FAIL]
  Notes: [Any issues?]

Test 2: Data Query (Router → SQL)
  Status: [PASS/FAIL]
  Latency: [X ms]
  Notes: [Any issues?]

Test 3: Documentation Query (Router → Support)
  Status: [PASS/FAIL]
  Latency: [X ms]
  Notes: [Any issues?]

Test 4: Infrastructure Query (Router → Azure Ops)
  Status: [PASS/FAIL]
  Latency: [X ms]
  Notes: [Any issues?]

Test 5: Composite Query (Router → SQL + Analytics)
  Status: [PASS/FAIL]
  Latency: [X ms]
  Notes: [Any issues?]

Test 6: Clarification (Ambiguous Query)
  Status: [PASS/FAIL]
  Notes: [Did router ask clarifying question?]

Overall: [SUCCESS/NEEDS WORK]
```

---

**Ready to test? Start with Test 1, then Test 2!**
