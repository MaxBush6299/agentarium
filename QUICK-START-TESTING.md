# 🚀 QUICK START - Test Thread Management (After Fixes)

## One Command to Test Everything

```powershell
# Stop backend (Ctrl+C in terminal if running)

# Restart backend with fixes
cd backend
python -m src.main
# Wait for: "INFO:     Application startup complete"

# In another terminal, refresh frontend
# Browser: http://localhost:5173/chat
```

---

## Expected Behavior Checklist

### ✅ Page Load
- [ ] Frontend loads without errors
- [ ] ThreadList sidebar shows "No conversations yet"
- [ ] "+" button visible and clickable

### ✅ Create Thread
- [ ] Click "+" button
- [ ] Thread appears in list instantly
- [ ] Thread has ID like `thread_abc123def456`
- [ ] Browser console shows no errors

### ✅ View Thread
- [ ] Click thread in list
- [ ] URL changes to `/chat/{threadId}`
- [ ] No 404 error in console
- [ ] Chat area ready for input

### ✅ Delete Thread
- [ ] Hover over thread, delete button appears
- [ ] Click delete, confirmation shows
- [ ] Click confirm, thread removed
- [ ] Navigates to `/chat` (no thread)

### ✅ Persistence
- [ ] Create thread
- [ ] Refresh page (F5)
- [ ] Thread still in list
- [ ] Data persists correctly

---

## Diagnostic Commands

### Check Backend is Running
```powershell
curl -X GET http://localhost:8000/api/agents?skip=0&limit=100
# Should return 200 OK with agent list
```

### Test Thread Creation
```powershell
curl -X POST http://localhost:8000/api/agents/support-triage/threads
# Should return 200 OK with thread object
```

### Test Thread List
```powershell
curl -X GET "http://localhost:8000/api/agents/support-triage/threads?limit=50"
# Should return 200 OK with threads array
```

### View Logs
```powershell
# Look for:
# - "Created thread {id}" ✅ Thread saved
# - "Listed N threads" ✅ Query worked
# - No "BadRequest" errors ✅ SQL syntax fixed
```

---

## Common Issues & Solutions

### Issue: Still Seeing 404
**Solution:** 
1. Backend not restarted - kill and restart
2. Clear browser cache - Hard refresh (Ctrl+Shift+R)
3. Check backend logs for errors

### Issue: Thread Not Persisting
**Solution:**
1. Cosmos DB not connected - Check connection string
2. Container not created - Run post-deploy script
3. Check logs for async errors

### Issue: API Response Error
**Solution:**
1. Clear frontend cache and rebuild
2. npm run dev to restart
3. Check network tab for response format

### Issue: "Sort is not a function"
**Solution:** Means fix #3 didn't apply properly
1. Verify chatService.ts has the response.threads extraction
2. Check that line 128 returns response.threads (not response)

---

## Expected Log Messages (Good Sign)

✅ These messages mean it's working:
```
INFO:     Application startup complete.
INFO:     127.0.0.1:xxxxx - "POST /api/agents/support-triage/threads HTTP/1.1" 200 OK
INFO:     Created thread thread_abcdefg123456 for agent support-triage
INFO:     127.0.0.1:xxxxx - "GET /api/agents/support-triage/threads?limit=50 HTTP/1.1" 200 OK
INFO:     Listed 1 threads (agent_id=support-triage, user_id=None)
INFO:     127.0.0.1:xxxxx - "GET /api/agents/support-triage/threads/thread_abcdefg123456 HTTP/1.1" 200 OK
```

❌ These messages mean something's wrong:
```
BadRequest - Syntax error, incorrect syntax near 'ROWS'  ← SQL not fixed
"POST /threads" 405 Method Not Allowed  ← Endpoint not added
TypeError: .sort is not a function  ← Response not extracted
Thread ... not found  ← Thread not persisted (async bug)
```

---

## Quick Feature Demo

```powershell
# 1. Create first thread
curl -X POST http://localhost:8000/api/agents/support-triage/threads

# Copy the returned "id" value

# 2. List all threads
curl -X GET "http://localhost:8000/api/agents/support-triage/threads?limit=50"

# 3. Get specific thread
curl -X GET "http://localhost:8000/api/agents/support-triage/threads/{id from step 1}"

# 4. Delete thread
curl -X DELETE "http://localhost:8000/api/agents/support-triage/threads/{id from step 1}"

# 5. Verify deleted
curl -X GET "http://localhost:8000/api/agents/support-triage/threads?limit=50"
# Should return empty threads array
```

---

## Browser Console Checks

Open DevTools (F12) → Console tab

### Good Signs ✅
```
No errors about:
- "Failed to load threads"
- "sort is not a function"
- "404 Not Found"
- Any network errors
```

### Bad Signs ❌
```
Error: Failed to load threads: AxiosError
TypeError: loadedThreads.sort is not a function
GET http://localhost:8000/api/... 404 Not Found
GET http://localhost:8000/api/... 500 Internal Server Error
```

---

## Files to Check If Issues Occur

1. **Backend won't start:**
   - `backend/src/api/chat.py` - POST endpoint added
   - `backend/src/persistence/threads.py` - Executor imports

2. **Threads not persisting:**
   - `backend/src/persistence/threads.py` - Check async/executor code
   - Backend logs for error messages

3. **Frontend errors:**
   - `frontend/src/services/chatService.ts` - Check listThreads function
   - Browser console for full error

4. **SQL errors:**
   - `backend/src/persistence/*.py` - Check all use LIMIT (not FETCH NEXT)

---

## Rollback Plan (If Needed)

If something goes wrong:
```bash
# Get previous version
git status
git log --oneline -5

# Revert problematic files
git checkout HEAD -- backend/src/api/chat.py
git checkout HEAD -- backend/src/persistence/threads.py
git checkout HEAD -- frontend/src/services/chatService.ts

# Restart
python -m src.main
```

---

## Success Criteria

✅ All tests pass when:
1. Thread creation works (POST returns thread with ID)
2. Thread list loads (GET returns array of threads)
3. Thread details work (GET specific thread returns data)
4. Thread deletion works (DELETE removes thread)
5. Frontend doesn't error (no 404, no TypeError)
6. Data persists (thread survives page refresh)

---

## That's It!

If all checks pass, Phase 3.7 is COMPLETE ✅

Next up: Advanced features, testing, deployment prep.

---

**Last Updated:** October 21, 2025  
**Status:** All fixes applied, ready for testing  
**Confidence Level:** High 🚀
