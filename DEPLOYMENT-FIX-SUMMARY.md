# Deployment Fix Summary: Missing Workflows in Production

## Problem
Workflows were not visible in the deployed frontend application, even though:
- Backend container logs showed workflow endpoints working correctly
- Backend was receiving successful requests to `/api/workflows/sequential-data-analysis/threads`
- Local development environment worked fine

## Root Cause Analysis

### Investigation Steps
1. ✅ Verified backend logs - all endpoints working
2. ✅ Confirmed workflows.py router registered in main.py
3. ✅ Found `/api/workflows` list endpoint implemented
4. ✅ Checked frontend code - correctly calling `/api/workflows`

### Discovery
The issue was in **frontend/nginx.conf** - it was missing a crucial configuration:

**Problem:** 
- Frontend makes fetch calls to `/api/workflows` (relative URL)
- In development (Vite), there's a proxy rule that forwards `/api/*` to `localhost:8000`
- In production (nginx serving SPA), there was **NO proxy configuration**
- nginx was treating `/api/*` as static files and returning 404
- Frontend couldn't load workflows because the API calls were failing silently

**Proof from nginx logs:**
- No proxy directive for `/api/` location
- Only had SPA routing and static file caching rules

## Solution

### Changes Made

**File: `frontend/nginx.conf`**

Added API proxy configuration that:
1. Intercepts all `/api/*` requests
2. Proxies them to `ca-backend-dev.internal:8000/api/`
3. Uses internal Container Apps DNS for service-to-service communication
4. Properly handles Server-Sent Events (disables buffering)
5. Preserves headers for authentication and tracing

```nginx
location /api/ {
    proxy_pass http://ca-backend-dev.internal:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Support for Server-Sent Events
    proxy_buffering off;
    proxy_cache_bypass $http_upgrade;
}
```

### Key Points

1. **Internal DNS** - `ca-backend-dev.internal` uses Container Apps environment's internal DNS
   - Both containers in same `containerAppsEnvironment` (cae-dev)
   - Service-to-service communication happens on private network
   - No need for external FQDN

2. **SSE Support** - Disabled buffering for streaming responses
   - Workflow execution uses Server-Sent Events
   - Default nginx buffering would delay/break streaming

3. **Header Preservation** - Forwards all necessary headers
   - Authentication tokens
   - X-Forwarded-* headers for logging/tracing
   - Connection upgrade for WebSocket (if used in future)

## Deployment

### Commit
```bash
git commit -m "[frontend] Add API proxy to backend container in nginx config"
```

### CI/CD Trigger
- Commit message contains `[frontend]` prefix
- GitHub Actions workflow `.github/workflows/deploy.yml` automatically triggers
- Steps:
  1. Build frontend Docker image from `frontend/Dockerfile`
  2. Push to Azure Container Registry (agentstatus.azurecr.io)
  3. Deploy to `ca-frontend-dev` container app
  4. Old container replaced with new one

### Expected Outcome
After deployment completes (5-10 minutes):
- Frontend will fetch workflows from backend API successfully
- `/api/workflows` requests will be proxied correctly
- Workflow list will display in AgentSelector component
- Users can select and use workflows normally

## Verification Steps

1. Open browser DevTools Network tab
2. Refresh the application
3. Look for `/api/workflows` request
   - Should return 200 OK with workflow data
   - Not 404 or connection error

4. Check if workflows appear in the dropdown selector
5. Try selecting "sequential-data-analysis" workflow
6. Verify conversation threads persist under that workflow

## Related Files Modified

- `frontend/nginx.conf` - Added proxy configuration
- `.github/workflows/deploy.yml` - Already configured to handle this (no changes needed)

## Technical Context

### Architecture
```
User Browser
    ↓
Frontend Container App (ca-frontend-dev)
    ├── nginx serving React SPA
    └── proxy /api → backend
    ↓ (internal network)
Backend Container App (ca-backend-dev)
    ├── FastAPI server on port 8000
    └── Provides /api endpoints
```

### Container Apps Environment
- Resource Group: `rg-agentdemo-dev`
- Environment Name: `cae-dev`
- Frontend: `ca-frontend-dev`
- Backend: `ca-backend-dev`
- Both on same vnet, can communicate via internal DNS names
