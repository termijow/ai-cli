---
name: fastapi-chat-endpoint-llama-cpp
description: Fix FastAPI backend /chat endpoint to call llama.cpp via HTTP instead of WebSocket
source: auto-skill
extracted_at: '2026-08-20T19:11:28.940Z'
---

## Problem

The FastAPI backend's `/chat` endpoint was attempting to use WebSocket connections to communicate with llama.cpp, but the frontend application was making standard HTTP POST requests instead.

Error symptoms:
- `TypeError: chat_with_llm() missing 1 required positional argument: 'websocket'`
- FastAPI endpoint raised HTTP 500 Internal Server Error

## Root Cause

The `/chat` endpoint in `server.py` was defined as:
```python
@app.post("/chat", tags=["Chat"])
async def chat_with_llm(message: str, websocket: WebSocket):
```

This required a WebSocket connection, which is only used for streaming responses. However, the frontend sends standard HTTP POST requests, not WebSocket connections.

Additionally, the llama.cpp server uses the model name `"localmodel"` (not `"qwen3.5-4b"`), which caused a 400 error when using the wrong model name.

## Solution

Refactor the `/chat` endpoint to make HTTP POST requests directly to llama.cpp's REST API instead of using WebSocket connections.

### Code Changes in `server.py`

**Before:**
```python
@app.post("/chat", tags=["Chat"])
async def chat_with_llm(message: str, websocket: WebSocket):
    """Chat with the LLM directly."""
    input_tokens = 0
    output_tokens = 0

    try:
        await websocket.accept()
        active_websockets[websocket.id] = websocket

        llm_response = call_llm(f"You are helpful assistant. {message}", max_tokens=512)

        async for chunk in llm_response:
            await websocket.send_json({"type": "stream", "data": chunk})
            input_tokens += 1
            output_tokens += len(chunk)

        await websocket.send_json({
            "type": "complete",
            "data": llm_response,
            "tokens_used": input_tokens + output_tokens
        })

    except WebSocketDisconnect:
        await websocket.close()
    except Exception as e:
        logger.error(f"Error during chat: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
```

**After:**
```python
@app.post("/chat", tags=["Chat"])
async def chat_with_llm(message: str):
    """Chat with the LLM directly."""
    import requests
    input_tokens = 0
    output_tokens = 0

    try:
        # Call llama.cpp v1/chat/completions endpoint
        test_url = f"http://localhost:{LLAMA_PORT}/v1/chat/completions"
        payload = {
            "model": "localmodel",
            "messages": [{"role": "user", "content": f"You are helpful assistant. {message}"}],
            "stream": False
        }
        response = requests.post(test_url, json=payload, timeout=10)
        data = response.json()

        llm_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        input_tokens = data.get("usage", {}).get("prompt_tokens", 0)
        output_tokens = data.get("usage", {}).get("completion_tokens", 0)

        return {
            "content": llm_response,
            "tokens_used": input_tokens + output_tokens
        }

    except Exception as e:
        logger.error(f"Error during chat: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
```

### Key Changes

1. **Removed `websocket` parameter** - No longer needed for non-streaming HTTP requests
2. **Added `requests.post()` call** - Makes direct HTTP POST to llama.cpp's REST API
3. **Changed model name** - `"localmodel"` instead of `"qwen3.5-4b"` (llama.cpp's actual model name)
4. **Used `messages` array** - llama.cpp's v1/chat/completions API uses the `messages` format
5. **Added `stream: False`** - Explicitly disable streaming for non-streaming requests
6. **Parse response correctly** - Extract content from `data["choices"][0]["message"]["content"]`

## When to Apply

When you need to:
1. Replace WebSocket-based streaming with standard HTTP requests
2. Call llama.cpp's REST API directly from a FastAPI backend
3. Support both frontend clients that use WebSocket and those that use HTTP POST

## API Format Reference

The llama.cpp server on port 1234 expects this format:
```json
{
  "model": "localmodel",
  "messages": [{"role": "user", "content": "your message"}],
  "stream": false
}
```

Response format:
```json
{
  "choices": [{
    "message": {"role": "assistant", "content": "..."},
    "usage": {"prompt_tokens": ..., "completion_tokens": ...}
  }]
}
```

## Related Skills

- `port-conflict-llama-cpp`: For separating FastAPI backend (port 3094) from llama.cpp (port 1234)
- `python-fastapi-llama-server-variable`: For managing llama.cpp server path configuration
