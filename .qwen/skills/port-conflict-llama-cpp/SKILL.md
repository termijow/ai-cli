---
name: port-conflict-llama-cpp
description: Fix FastAPI server port conflict with llama.cpp server when using same port
source: auto-skill
extracted_at: '2026-08-20T18:54:12.067Z'
---

## Problem

The FastAPI backend server failed to start due to a port conflict. The backend server attempted to bind to port 1234 (configured as `LLAMA_PORT`), but that port was already occupied by the llama.cpp server process running on `localhost:1234`.

Error symptoms:
- Backend server could not start: `Address already in use`
- Port 1234 was already in use by process pid=385892 (llama.cpp server)

## Root Cause

In `server.py` line 757:
```python
uvicorn.run("server:app", host="0.0.0.0", port=LLAMA_PORT, ...)
```

The backend server was configured to use `LLAMA_PORT` (which defaults to 1234) for its own uvicorn server. However, the backend server needs to make HTTP calls to llama.cpp on port 1234, not run its own server on that port.

This created a conflict where:
1. llama.cpp server is running on port 1234 (providing LLM inference)
2. FastAPI backend server tried to bind to port 1234 (for its own HTTP server)
3. Port 1234 can only be bound by one process

## Solution

Change the backend server's uvicorn port to a different port (3094) while keeping the llama.cpp connection port at 1234.

### Code Changes in `server.py`

**Before (line 757):**
```python
uvicorn.run("server:app", host="0.0.0.0", port=LLAMA_PORT, reload=False, workers=1, log_level="info")
```

**After:**
```python
uvicorn.run("server:app", host="0.0.0.0", port=3094, reload=False, workers=1, log_level="info")
```

The `LLAMA_PORT` constant (used only for llama.cpp API calls in the `call_llm()` function) remains at 1234:
```python
LLAMA_PORT = os.environ.get("LLAMA_PORT", 1234)
```

### Connection Pattern

- **llama.cpp server**: Runs on `http://localhost:1234/v1/chat/completions`
- **FastAPI backend server**: Runs on `http://localhost:3094`
- **Communication**: Backend makes HTTP requests to llama.cpp on port 1234

## When to Apply

When you need to:
1. Use llama.cpp server via FastAPI backend
2. Both services would otherwise use the same port
3. Backend needs to call llama.cpp API, not run its own server on that port

## Port Selection Guidelines

- Use a port in the 3000-3999 range for FastAPI backend (common convention)
- Keep llama.cpp ports in the 1000-2000 range (common for llama.cpp servers)
- Document the port assignments in the project README

## Related Skills

- `python-fastapi-llama-server-variable`: For managing llama.cpp server path variables
- `ai-cli-services-startup`: For starting backend services with startup scripts
