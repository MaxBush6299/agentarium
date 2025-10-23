# Router Agent - Quick Reference Card

## 📍 One-Page Cheat Sheet

### What We Built
Multi-agent orchestrator using A2A protocol that intelligently routes user queries to specialized agents.

---

### Agent Overview

```
ROUTER (Orchestrator)
├─ → SQL Agent (Database queries)
├─ → Support Triage (Documentation)
├─ → Azure Ops (Infrastructure)
└─ → Data Analytics (BI/Reports)
```

---

### Quick Test

**Start backend:**
```bash
cd backend && python -m uvicorn src.main:app --reload
```

**Simple test:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "router",
    "message": "Show me top customers from Adventure Works",
    "thread_id": "test-1"
  }'
```

**Expected:** Router calls SQL Agent, returns customer list

---

### Query Examples

| Query | Routes To | Why |
|-------|-----------|-----|
| "Show Q4 sales data" | SQL Agent | Database query |
| "Create a dashboard" | Data Analytics | Business intelligence |
| "How do I...?" | Support Triage | Documentation |
| "Check my Azure resources" | Azure Ops | Infrastructure |
| "Get sales data AND analyze it" | SQL + Analytics | Composite |

---

### Files Changed

- ✅ `seed_agents.py` - Added Router with 4 A2A tools

### Documentation Created

- 📄 `ROUTER-AGENT-IMPLEMENTATION.md` - Technical details
- 📄 `ROUTER-AGENT-VISUAL-GUIDE.md` - Diagrams & examples
- 📄 `ROUTER-AGENT-TESTING.md` - Test cases & debugging
- 📄 `PHASE-4-0-ROUTER-SUMMARY.md` - Full summary

---

### A2A Tool Configuration

Each specialist is configured as an A2A tool in Router:

```python
ToolConfig(
    type=ToolType.A2A,        # A2A protocol
    name="sql-agent",         # Tool name
    a2a_agent_id="sql-agent", # Target agent
    enabled=True
)
```

---

### System Prompt Key Concepts

Router knows:
- SQL Agent handles database queries
- Azure Ops handles infrastructure
- Support Triage handles documentation
- Data Analytics handles insights/reports
- Can call multiple agents if needed
- Should ask clarifying questions if unclear

---

### Testing Checklist

- [ ] Backend starts successfully
- [ ] Router Agent loads (check /api/agents/router)
- [ ] Simple query routes to SQL Agent
- [ ] Documentation query routes to Support Triage
- [ ] Infrastructure query routes to Azure Ops
- [ ] Composite query calls multiple agents
- [ ] Ambiguous query asks for clarification

---

### Debug Commands

**Check if Router exists:**
```bash
curl http://localhost:8000/api/agents/router | grep -i router
```

**Check all agents:**
```bash
curl http://localhost:8000/api/agents/ | grep -i '"id"'
```

**Watch logs:**
```bash
tail -f backend.log | grep -i "router\|a2a"
```

---

### Expected Behavior

**User sends query** ➜ **Router analyzes** ➜ **Routes to specialist** ➜ **Specialist executes** ➜ **Results returned**

---

### Latency Expectations

- Simple query: 2-5 seconds
- Composite query: 4-10 seconds
- Ambiguous query: 1-2 seconds (asks clarification)

---

### What to Look For in Response

✅ Router acknowledges routing decision  
✅ Specialist agent name mentioned  
✅ Results from specialist included  
✅ Response is relevant to query  
✅ No errors in response  

---

### Common Issues

| Issue | Fix |
|-------|-----|
| Router not found | Restart backend (seeds on startup) |
| A2A tools not loading | Check ToolRegistry for A2A support |
| A2A call fails | Verify specialist agent is ACTIVE |
| Timeout | Check specialist execution time |

---

### Next Steps

1. **Test locally** with test queries
2. **Validate A2A** calls work end-to-end
3. **Refine routing** logic based on results
4. **Build Azure Storage tool** (deferred)
5. **Test SQL → Analytics** chain

---

### Key Files

- `seed_agents.py` - Router Agent configuration
- `models.py` - ToolType.A2A enum
- `a2a/api.py` - A2A protocol endpoints
- `agents/factory.py` - Creates agents from metadata
- `agents/tool_registry.py` - Loads tools including A2A

---

### Architecture Pattern

```
Request Flow:
User Query
    ↓
Router (Orchestrator)
    ↓ (A2A Protocol)
Specialist Agent
    ↓
Result to User
```

**Key:** Each component independent, standardized communication via A2A

---

### Success Criteria

✅ Router routes correctly 80%+  
✅ A2A calls 100% successful  
✅ Response time < 5 seconds  
✅ No exceptions in logs  
✅ Multi-agent chains work  

---

**Status:** ✅ Ready to test!  
**Time to implement:** ~1.5 hours (completed)  
**Time to test:** ~1 hour (next)  
**Time for Azure Storage:** ~2.5-3 hours (deferred)

---

See full documentation in:
- ROUTER-AGENT-IMPLEMENTATION.md
- ROUTER-AGENT-VISUAL-GUIDE.md
- ROUTER-AGENT-TESTING.md
