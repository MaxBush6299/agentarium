# Phase 3.7 Backend Integration Guide

**Date:** October 21, 2025  
**Status:** Frontend complete, backend integration required  

## Current Status

✅ **Frontend:** ThreadList component implemented and ready  
❌ **Backend:** GET `/api/agents/{agentId}/threads` returning 500 error  

## Problem Analysis

### Error
```
GET http://localhost:8000/api/agents/support-triage/threads?limit=50 500 (Internal Server Error)
```

### Root Cause
The backend endpoint exists but is failing. Most likely causes:

1. **Cosmos DB Not Initialized**
   - Database `agents-db` doesn't exist
   - Container `threads` doesn't exist
   - Connection string is invalid

2. **Azure Cosmos DB Service Issue**
   - Emulator not running (if using local emulator)
   - Database credentials invalid
   - Network connectivity issue

3. **Code Issue**
   - SQL query has syntax error
   - Thread model doesn't match Cosmos DB structure

## Solution Steps

### Step 1: Verify Backend is Running

```powershell
# Check if backend is running
curl -s http://localhost:8000/api/health

# Expected response: {"status": "ok"}
```

### Step 2: Verify Cosmos DB Setup

#### Option A: Using Azure Cosmos DB Emulator (Development)

```powershell
# Install emulator (if not already installed)
# https://learn.microsoft.com/en-us/azure/cosmos-db/local-emulator-export-ssl-certificates

# Start emulator (or ensure it's running)
# Default connection string: AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTjd3K+tzjl5T45CpFsom1O7Hq/RQShnBVGg==
```

#### Option B: Using Azure Cosmos DB in Cloud

```powershell
# Get connection string from Azure
$accountName = "cosmosdb-agents-dev"
$resourceGroup = "rg-agentdemo-dev"

# Get the connection string
az cosmosdb keys list \
  --name $accountName \
  --resource-group $resourceGroup \
  --type connection-strings

# Set in backend environment variables
$env:COSMOS_CONNECTION_STRING = "AccountEndpoint=...;AccountKey=..."
```

### Step 3: Verify Database and Container Setup

```powershell
# Run post-deployment setup to create containers
cd infra
.\post-deploy-setup.ps1 -Environment dev
```

This will:
- Create `agents-db` database
- Create `threads` container with partition key `/agentId`
- Create other required containers (`runs`, `steps`, `agents`)

### Step 4: Check Backend Logs

```powershell
# Run backend with verbose logging
cd backend
python -m src.main 2>&1 | Tee-Object -FilePath backend.log

# Check for errors like:
# - "Cosmos DB client not initialized"
# - "Error listing threads"
# - Connection errors
```

### Step 5: Test API Directly

```powershell
# Test the threads endpoint
curl -X GET "http://localhost:8000/api/agents/support-triage/threads?limit=50" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "threads": [],
#   "total": 0,
#   "page": 1,
#   "page_size": 50
# }
```

## Implementation Details

### Backend Endpoint
**Path:** `GET /api/agents/{agent_id}/threads`  
**Handler:** `backend/src/api/chat.py::list_threads()`  
**Repository:** `backend/src/persistence/threads.py::ThreadRepository.list()`  

### Query Parameters
```
limit:  int (1-100, default: 50)  - Max threads to return
offset: int (≥0, default: 0)      - Threads to skip for pagination
status: str (default: "active")   - Filter by status
```

### Response Schema
```typescript
interface ThreadListResponse {
  threads: ChatThread[]  // List of thread objects
  total: number         // Total thread count
  page: number          // Current page number
  page_size: number     // Threads per page
}
```

### ChatThread Model
```typescript
interface ChatThread {
  id: string           // "thread_xxxxx"
  agent_id: string     // Agent this thread belongs to
  status: string       // "active" | "archived" | "deleted"
  title?: string       // Conversation title
  created_at: string   // ISO timestamp
  updated_at: string   // ISO timestamp
  metadata?: object    // Custom metadata
  messages: []         // Messages in thread (often empty in list)
}
```

## Expected Behavior After Fix

### Frontend
1. ✅ ThreadList component loads successfully
2. ✅ Shows "No conversations yet" (empty state)
3. ✅ "New Conversation" button creates first thread
4. ✅ Created thread appears in list
5. ✅ Can switch between threads
6. ✅ Can delete threads
7. ✅ Threads persist across page refreshes

### Backend
1. ✅ `GET /api/agents/{id}/threads` returns 200
2. ✅ Returns empty array initially
3. ✅ Returns threads after creation
4. ✅ Supports pagination
5. ✅ Filters by status
6. ✅ Proper error handling for missing threads

## Quick Start (Local Development)

### Using Cosmos DB Emulator

```powershell
# 1. Start Cosmos Emulator (if not already running)
# Launch from Start menu or:
# & "C:\Program Files\Azure Cosmos DB Emulator\CosmosDB.Emulator.exe"

# 2. Verify emulator connection
curl -X GET "https://localhost:8081/_explorer/index.html"

# 3. Set backend environment variable
$env:COSMOS_CONNECTION_STRING = "AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTjd3K+tzjl5T45CpFsom1O7Hq/RQShnBVGg=="

# 4. Create containers
cd infra
.\create-cosmos-collections.ps1 -Environment local

# 5. Start backend
cd ../backend
python -m src.main

# 6. Start frontend
cd ../frontend
npm run dev

# 7. Navigate to http://localhost:5173/chat
# Should see "No conversations yet" in sidebar
```

### Using Azure Resources

```powershell
# 1. Get connection string
$connStr = az cosmosdb keys list \
  --name cosmosdb-agents-dev \
  --resource-group rg-agentdemo-dev \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" \
  -o tsv

# 2. Set environment
$env:COSMOS_CONNECTION_STRING = $connStr

# 3. Create containers (if needed)
cd infra
.\post-deploy-setup.ps1 -Environment dev

# 4. Start backend and frontend
```

## Troubleshooting

### Error: "Cosmos DB client not initialized"
**Cause:** Connection string not set or invalid  
**Fix:** 
- Check `COSMOS_CONNECTION_STRING` environment variable
- Verify connection string format
- Restart backend after setting env var

### Error: "Container not found"
**Cause:** `threads` container doesn't exist in database  
**Fix:**
- Run `post-deploy-setup.ps1` script
- Or run `create-cosmos-collections.ps1` script

### Error: "Invalid query syntax"
**Cause:** Cosmos DB SQL syntax error (rare)  
**Fix:**
- Check logs for exact SQL query
- Verify SQL syntax (Cosmos uses SQL-like syntax)
- File issue with query builder

### Error: "Network timeout"
**Cause:** Connection to Cosmos DB failing  
**Fix:**
- Verify Cosmos DB is running/accessible
- Check network connectivity
- Try localhost/emulator first

## Next Steps

1. **Immediate:** Set up Cosmos DB and verify endpoint returns 200
2. **Short term:** Test thread creation and deletion
3. **Validation:** Run full integration test suite
4. **Documentation:** Update API docs with examples

## Files Modified

- ✅ `frontend/src/components/chat/ThreadList.tsx` - Better error messages
- ✅ `frontend/src/services/chatService.ts` - Uses axios client
- ✅ `frontend/src/pages/ChatPage.tsx` - Integrated ThreadList
- 🔄 `backend/src/api/chat.py` - Existing (no changes needed)
- 🔄 `backend/src/persistence/threads.py` - Existing (no changes needed)

## References

- [Cosmos DB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/local-emulator)
- [Cosmos DB SQL Reference](https://learn.microsoft.com/en-us/azure/cosmos-db/sql-query)
- [Azure Cosmos DB Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/cosmos)

## Support

If issues persist after following these steps:

1. Check backend logs: `backend.log`
2. Test with `curl` command above
3. Verify Cosmos DB connectivity
4. Check authentication credentials
5. File issue with error details and logs
