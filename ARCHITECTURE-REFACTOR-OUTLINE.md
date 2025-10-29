# API Architecture Refactor Outline

## Vision
Restructure the Chat API to support two distinct modes:
1. **Individual Agent Chat** - Direct conversation with specific agents (top section)
2. **Multi-Agent Workflows** - Orchestrated conversations using HandoffBuilder (bottom section)

## Current State
- **Single router agent**: `/api/agents/router/chat` was routing to specialists
- **Multiple agent endpoints**: `/api/agents/{agent_id}/chat` for direct agent access
- **Custom handoff code**: `handoff_router.py`, `handoff_orchestrator.py`, `intelligent_orchestrator.py` (legacy)
- **New HandoffBuilder**: `handoff_builder_orchestrator.py` (production-ready, official pattern)

---

## Phase 1: Code Cleanup & Organization

### Task 1.1: Create Archive Folder
- **Location**: `backend/src/agents/archive/`
- **Action**: Archive legacy handoff implementations:
  - `handoff_router.py` → `archive/handoff_router.py` (custom routing logic)
  - `handoff_orchestrator.py` → `archive/handoff_orchestrator.py` (custom orchestration)
  - `intelligent_orchestrator.py` → `archive/intelligent_orchestrator.py` (failed attempt)
- **Keep**: `handoff_builder_orchestrator.py` (official pattern)
- **Reason**: These are replaced by official HandoffBuilder. Archive for reference but don't use.

### Task 1.2: Remove Legacy Imports
- **File**: `backend/src/api/chat.py`
- **Action**: Remove import of `HandoffRouter`:
  ```python
  # REMOVE: from src.agents.handoff_router import HandoffRouter
  ```
- **Impact**: No longer needed with new architecture

### Task 1.3: Update Chat API Docstring
- **File**: `backend/src/api/chat.py`
- **Action**: Update module docstring to reflect new architecture
- **Content**:
  ```
  Chat API Router
  RESTful API endpoints for:
  1. Individual agent conversations (direct chat)
  2. Multi-agent workflow orchestration (HandoffBuilder)
  
  Both support SSE streaming for real-time responses.
  ```

---

## Phase 2: Individual Agent Chat (Section 1)

### Task 2.1: Verify Individual Agent Endpoints Work
- **Endpoint**: `POST /api/agents/{agent_id}/chat`
- **Available Agents**: data-agent, analyst, order-agent, evaluator
- **Note**: Router is NOT available for direct chat (coordinator-only)
- **Action**: Test each agent directly (no handoff)
- **Expected**: Each agent responds independently without routing to others
- **Files Involved**: 
  - `src/api/chat.py` - Existing endpoint (add router rejection check)
  - `src/agents/factory.py` - Agent creation (no changes needed)

### Task 2.2: Update Agent Endpoint to Reject Router
- **File**: `backend/src/api/chat.py`
- **Change**: In POST `/api/agents/{agent_id}/chat`, add check:
  ```python
  if agent_id == "router":
      raise HTTPException(status_code=403, detail="Router agent only available via /api/workflows")
  ```
- **Impact**: Users cannot directly chat with router

### Task 2.3: Document Individual Agent Usage
- **File**: Create `docs/API-INDIVIDUAL-AGENTS.md`
- **Content**:
  - List all 4 available agents with IDs and descriptions
  - Example curl requests for each
  - Response format examples
  - Tool availability per agent

---

## Phase 3: Multi-Agent Workflows (Section 2)

### Detailed Requirements (from user clarification)

**Individual Agents** (direct chat only):
- data-agent
- analyst
- order-agent
- evaluator

**Router** - Excluded from individual chat, used as workflow coordinator

**Workflow Participants**:
- router (coordinator)
- data-agent
- analyst
- order-agent
- evaluator

**Workflow Routing Rules**:
1. Router classifies intent and routes to specialist (data-agent, analyst, or order-agent)
2. **CONSTRAINT**: If data-agent is used → must route to analyst next
3. All paths end with evaluator
4. If evaluator unsatisfied → route back to router (loop up to max_handoffs times)
5. Max handoffs reached → return evaluator response + "Max attempts reached" message
6. Handoff path visualized in trace panel

**Response Format**:
- **Chat**: Just final message
- **Trace Panel**: All metadata (handoff_path, tool_calls, timestamps, satisfaction_score, evaluator_reasoning)

**Request Format**:
```json
{
  "message": "user query",
  "thread_id": "required_string",
  "max_handoffs": 3
}
```

**Thread Storage**: Same as individual agents with optional `workflow_id` field

---

### Task 3.1: Update Agent Registry
- **File**: `backend/src/agents/registry.py` or agent repository
- **Action**: Mark router as "coordinator_only" (not available for direct chat)
- **Impact**: `/api/agents/router/chat` should return 403 or redirect to workflows endpoint

### Task 3.2: Create Workflows Namespace
- **Location**: `backend/src/agents/workflows/`
- **Action**: Create new directory for workflow implementations
- **Contents**:
  - `__init__.py`
  - `handoff_workflow.py` - Main HandoffBuilder workflow implementation
  - `workflow_models.py` - Pydantic models for workflow requests/responses
  - `workflow_registry.py` - Registry of available workflows
  - `workflow_orchestrator.py` - Orchestrator for managing workflow execution

### Task 3.3: Create Workflow Registry
- **File**: `backend/src/agents/workflows/workflow_registry.py`
- **Purpose**: Define available workflows and their metadata
- **Content**:
  ```python
  WORKFLOWS = {
      "intelligent-handoff": {
          "id": "intelligent-handoff",
          "name": "Intelligent Handoff Workflow",
          "description": "Multi-tier routing with quality evaluation and intelligent re-routing",
          "coordinator": "router",
          "participants": ["router", "data-agent", "analyst", "order-agent", "evaluator"],
          "max_handoffs": 3,
          "routing_rules": {
              "data_agent_requires_analyst": true,
              "always_end_with_evaluator": true,
              "allow_reroute_if_unsatisfied": true
          }
      }
  }
  ```

### Task 3.4: Implement Workflow Models
- **File**: `backend/src/agents/workflows/workflow_models.py`
- **Models**:
  ```python
  WorkflowRequest:
    message: str
    thread_id: str  # required
    max_handoffs: int = 3  # optional override
  
  WorkflowResponse:
    workflow_id: str
    final_response: str
    primary_agent: str
    handoff_path: List[str]  # ["router", "data-agent", "analyst", "evaluator"]
    satisfaction_score: Optional[float]
    evaluator_reasoning: Optional[str]
    max_attempts_reached: bool
    
  WorkflowTraceMetadata:
    handoff_path: List[str]
    all_tool_calls: List[Dict]  # from all agents in workflow
    agent_timestamps: Dict[str, float]  # agent -> execution time
    evaluator_assessment: str
    satisfaction_score: float
  ```

### Task 3.5: Create Workflow Orchestrator
- **File**: `backend/src/agents/workflows/workflow_orchestrator.py`
- **Purpose**: Manage workflow execution with HandoffBuilder
- **Responsibilities**:
  - Initialize HandoffBuilder with router as coordinator
  - Apply routing constraints (data-agent → analyst, always end with evaluator)
  - Track handoff path and metadata
  - Handle max_handoffs limit
  - Extract final response and all metadata
- **Key Methods**:
  - `async def execute(message: str, thread_id: str, max_handoffs: int) -> WorkflowResponse`
  - `_build_handoff_graph()` - Define routing rules
  - `_extract_metadata()` - Collect trace data

### Task 3.6: Implement Workflow Handler
- **File**: `backend/src/agents/workflows/handoff_workflow.py`
- **Purpose**: High-level workflow runner
- **Responsibilities**:
  - Load agents from database
  - Create/get thread with workflow_id
  - Call orchestrator
  - Format response and metadata
- **Key Method**: `async def run_workflow(message: str, thread_id: str, max_handoffs: int) -> Tuple[str, WorkflowTraceMetadata]`

### Task 3.7: Create Workflow Chat API Endpoint
- **File**: `backend/src/api/chat.py` (add new endpoint)
- **Endpoint**: `POST /api/workflows/{workflow_id}/chat`
- **Path Parameters**:
  - `workflow_id`: ID of workflow (e.g., "intelligent-handoff")
- **Request Body**: `WorkflowRequest`
- **Response**: `StreamingResponse` with SSE events
- **Logic**:
  1. Validate workflow_id exists in registry
  2. Load/create thread with workflow_id
  3. Stream initial status event
  4. Call workflow handler
  5. For each agent in path: stream trace event with agent name, input, output
  6. Stream final message
  7. Stream metadata event (handoff_path, satisfaction_score, evaluator_reasoning)
  8. Stream done event

### Task 3.8: Update Individual Agent Endpoint
- **File**: `backend/src/api/chat.py`
- **Change**: Add check to reject `agent_id == "router"`
- **Response**: 403 Forbidden with message: "Router agent only available via /api/workflows"

### Task 3.9: Create Workflows List Endpoint
- **File**: `backend/src/api/chat.py` (add new endpoint)
- **Endpoint**: `GET /api/workflows`
- **Response**: List of available workflows with full metadata
- **Purpose**: Discovery - client can see what workflows are available and their routing rules

### Task 3.10: Extend Thread Model (Optional)
- **File**: `backend/src/persistence/models.py`
- **Change**: Add optional `workflow_id` field to `Thread` model
- **Purpose**: Track which workflow a thread belongs to
- **Migration**: Not required (existing threads will have null)

---

## Phase 4: Thread Management Updates

### Task 4.1: Extend Thread Model
- **File**: `backend/src/persistence/models.py`
- **Change**: Add `workflow_id` field to `Thread` model
- **Purpose**: Track which workflow a thread belongs to
- **Migration**: Optional (existing threads won't have it)

### Task 4.2: Thread Repository Updates
- **File**: `backend/src/persistence/threads.py`
- **Change**: Support creating threads with workflow context
- **Method**: Add optional `workflow_id` parameter to create()

---

## Phase 5: Frontend Integration

### Task 5.1: Update Agent Selector
- **File**: `frontend/src/components/chat/ChatPage.tsx`
- **Change**: Split agent selector into two sections:
  ```
  INDIVIDUAL AGENTS
  - Data Agent
  - Analyst
  - Order Agent
  - Microsoft Docs
  - Evaluator
  
  MULTI-AGENT WORKFLOWS
  - Intelligent Handoff
  ```

### Task 5.2: Update API Call Logic
- **File**: `frontend/src/hooks/useChat.ts`
- **Change**: Detect if user selected a workflow vs individual agent
- **Logic**:
  - If individual agent: `POST /api/agents/{agent_id}/chat`
  - If workflow: `POST /api/workflows/{workflow_id}/chat`

### Task 5.3: Add Workflow Metadata Display
- **File**: `frontend/src/components/chat/MessageBubble.tsx`
- **Change**: Show workflow metadata when available
- **Display**:
  - Primary agent used
  - Handoff path (breadcrumb: router → data-agent → evaluator)
  - Satisfaction score

---

## Phase 6: Testing & Validation

### Task 6.1: Unit Tests - Individual Agents
- **File**: `backend/tests/unit/test_individual_agents.py`
- **Tests**:
  - Each agent responds correctly
  - No unexpected handoffs occur
  - Tools work as expected per agent

### Task 6.2: Integration Tests - Workflow
- **File**: `backend/tests/integration/test_handoff_workflow.py`
- **Tests**:
  - Router correctly classifies intent
  - Handoffs to correct specialists
  - Evaluator assesses satisfaction
  - Re-routing works when unsatisfied
  - Max handoff limit enforced (3)
  - Response quality is acceptable

### Task 6.3: End-to-End Tests
- **File**: `backend/tests/integration/test_e2e_workflows.py`
- **Scenarios**:
  - Query requiring data retrieval → data-agent → evaluator
  - Query requiring analysis → router → data-agent → analyst → evaluator
  - Query with satisfaction on first response
  - Query with re-routing for better answer

### Task 6.4: Frontend Tests
- **File**: `frontend/tests/integration/test_workflow_selection.spec.ts`
- **Tests**:
  - Individual agent section works
  - Workflow section appears and is selectable
  - Correct API endpoint called
  - Workflow metadata displays correctly

---

## Phase 7: Documentation

### Task 7.1: Update API Documentation
- **File**: `docs/API-ENDPOINTS.md`
- **Sections**:
  - Individual Agents
    - List all agents
    - POST /api/agents/{agent_id}/chat examples
  - Multi-Agent Workflows
    - GET /api/workflows (list available)
    - POST /api/workflows/{workflow_id}/chat examples
    - Response format with metadata

### Task 7.2: Architecture Decision Record
- **File**: `docs/ARCHITECTURE-DECISIONS.md`
- **Content**:
  - Why we split individual vs workflow
  - Why HandoffBuilder over custom code
  - Future workflow addition pattern
  - Migration path for old code

### Task 7.3: Workflow Configuration Guide
- **File**: `docs/WORKFLOW-CONFIGURATION.md`
- **Content**:
  - How to add new workflows
  - How to modify existing workflow routing
  - How to update agent composition
  - Monitoring and debugging workflows

---

## Phase 8: Deployment & Migration

### Task 8.1: Update Bicep Infrastructure
- **File**: `infra/main.bicep`
- **Change**: No infrastructure changes needed (same backend)
- **Note**: Document the API structure change

### Task 8.2: Update GitHub Actions
- **File**: `.github/workflows/deploy.yml`
- **Change**: Archive step (if deploying old files)
- **Note**: Document that old handoff code is archived

### Task 8.3: Update Container Image
- **Action**: Rebuild backend container with:
  - Archived legacy code (for reference)
  - New workflows directory
  - Updated requirements (agent-framework>=0.45.0)

### Task 8.4: Update Deployment Documentation
- **File**: `DEPLOYMENT.md`
- **Sections**:
  - New API structure
  - Feature flags (none needed initially)
  - Rollback strategy (none needed - backward compatible)

---

## Dependency Graph

```
Phase 1 (Cleanup)
├── Task 1.1: Create Archive
├── Task 1.2: Remove Imports
└── Task 1.3: Update Docstrings

Phase 2 (Individual Agents)
└── Task 2: Already working, just verify

Phase 3 (Multi-Agent Workflows)
├── Task 3.1: Create workflows directory
├── Task 3.2: Create registry
├── Task 3.3: Create models
├── Task 3.4: Create handler
├── Task 3.5: Create endpoint
└── Task 3.6: List endpoint

Phase 4 (Thread Management)
└── Tasks 4.1-4.2: Optional updates

Phase 5 (Frontend)
├── Task 5.1: Agent selector
├── Task 5.2: API logic
└── Task 5.3: Metadata display

Phase 6 (Testing)
├── Task 6.1-6.4: Various tests

Phase 7 (Documentation)
├── Task 7.1-7.3: Various docs

Phase 8 (Deployment)
└── Tasks 8.1-8.4: Deployment steps
```

---

## Execution Priority

**High Priority (Must Complete)**
1. Phase 1: Code cleanup & archive legacy code
2. Phase 3: Multi-agent workflows implementation
3. Phase 6.1-6.2: Core testing

**Medium Priority (Should Complete)**
4. Phase 5: Frontend integration
5. Phase 6.3-6.4: End-to-end testing
6. Phase 7: Documentation

**Low Priority (Nice to Have)**
7. Phase 4: Thread management updates
8. Phase 8: Deployment & migration docs

---

## Success Criteria

✅ **Individual agents** can be chatted with directly  
✅ **Multi-agent workflows** can be started and complete successfully  
✅ **API has two distinct sections** visible in discovery  
✅ **Legacy code archived** but not deleted  
✅ **Frontend shows both options** clearly separated  
✅ **Tests pass** for both modes  
✅ **Documentation updated** for new structure  
✅ **Deployment works** without issues  

---

## Timeline Estimate

- Phase 1-2: 30 min (cleanup + verify)
- Phase 3: 2 hours (implement workflow infrastructure)
- Phase 5: 1.5 hours (frontend updates)
- Phase 6-7: 2 hours (testing + docs)
- Phase 8: 1 hour (deployment prep)

**Total: ~6.5 hours**

---

## Next Steps

1. **Approve outline** - Make any changes to priority/scope
2. **Start Phase 1** - Archive legacy code
3. **Implement Phase 3** - Create workflow infrastructure
4. **Test Phase 6** - Validate implementation
5. **Update Phase 5** - Frontend integration
