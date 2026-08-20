#!/usr/bin/env python3
"""
ai-cli backend server - FastAPI server with llama.cpp integration
"""

import asyncio
import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Model configuration
MODEL_PATH = PROJECT_ROOT / "models" / "Qwen3.5-9B-GGUF" / "Qwen3.5-9B-GGUF.Q4_K_M.gguf"
LLAMA_CPP_SERVER = PROJECT_ROOT / "llama-server"
LLAMA_PORT = os.environ.get("LLAMA_PORT", 8080)
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# Global FastAPI app
app = FastAPI(title="AI CLI Backend", description="Backend API for AI document processing", version="1.0.0")
active_websockets: Dict[str, WebSocket] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Starting AI CLI Backend server...")
    logger.info(f"Model path: {MODEL_PATH}")
    logger.info(f"LLAMA_CPP_SERVER: {LLAMA_SERVER}")
    
    # Start websocket savings handler in background
    from bin.websocket_savings_handler import SavingsServer
    savings_server = SavingsServer()
    savings_task = asyncio.create_task(savings_server.start())
    
    yield
    
    logger.info("Shutting down AI CLI Backend server...")
    savings_task.cancel()
    try:
        await savings_task
    except asyncio.CancelledError:
        pass
    
    for ws in active_websockets.values():
        await ws.close()
    
    logger.info("Server shutdown complete")


# Pydantic models
class DocumentOperation(BaseModel):
    """Request body for document operations."""
    operation: str = Field(..., description="Operation: summarize, translate, modify, extract")
    document_type: str = Field(..., description="Type: pdf, docx, md, text")
    content: Optional[str] = Field(None, description="Document content if file not provided")
    file_path: Optional[str] = Field(None, description="Path to document file")
    language: Optional[str] = Field(None, description="Source/target language for translation")
    prompt: Optional[str] = Field(None, description="Custom prompt for operation")
    max_tokens: Optional[int] = Field(2048, description="Maximum output tokens")


class TokenTracking(BaseModel):
    """Token tracking for savings calculation."""
    input_tokens: int = 0
    output_tokens: int = 0

# Endpoints

@app.on_event("startup")
async def startup_event():
    """Startup event - initialize llama.cpp connection."""
    logger.info("Starting backend server...")
    logger.info(f"Model: {MODEL_PATH}")
    logger.info(f"LLAMA_CPP_SERVER: {LLAMA_SERVER}")
    
    try:
        import requests
        test_url = f"http://localhost:{LLAMA_PORT}/v1/chat/completions"
        headers = {"Accept": "application/json"}
        response = requests.post(test_url, headers=headers, timeout=5)
        if response.status_code == 200:
            logger.info("Successfully connected to llama.cpp server")
        else:
            logger.warning(f"llama.cpp server returned {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not connect to llama.cpp server: {e}")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-cli-backend"}


@app.get("/model/info", tags=["Model"])
async def model_info():
    """Return information about the loaded model."""
    try:
        import requests
        test_url = f"http://localhost:{LLAMA_PORT}/v1/models"
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            return {
                "status": "success",
                "model": response.json().get("root", {}),
                "server": f"http://localhost:{LLAMA_PORT}"
            }
    except Exception as e:
        logger.warning(f"Could not fetch model info: {e}")
    return {
        "status": "success",
        "model": {
            "path": str(MODEL_PATH),
            "name": "Qwen3.5-9B-GGUF",
            "quantization": "Q4_K_M"
        }
    }


@app.post("/documents/{document_type}/summarize", tags=["Documents"])
async def summarize_document(document_type: str, request: DocumentOperation, websocket: WebSocket):
    """Summarize a document of the specified type."""
    if document_type not in ["pdf", "docx", "md", "text"]:
        raise HTTPException(400, "Invalid document type")
    
    input_tokens = 0
    output_tokens = 0
    
    try:
        await websocket.accept()
        active_websockets[websocket.id] = websocket
        
        content = None
        if request.file_path:
            content = read_file_content(request.file_path)
        elif request.content:
            content = request.content
        
        if not content:
            raise HTTPException(400, "No content provided")
        
        prompt = create_summarize_prompt(content, request.prompt)
        llm_response = call_llm(prompt, max_tokens=request.max_tokens or MAX_TOKENS)
        
        async for chunk in llm_response:
            await websocket.send_json({"type": "stream", "data": chunk})
            input_tokens += 1
            output_tokens += len(chunk)
        
        await websocket.send_json({
            "type": "complete",
            "data": llm_response,
            "tokens_used": input_tokens + output_tokens
        })
        
        await websocket.send_json({
            "type": "tokens_update",
            "data": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "savings": 0.000015,
                "timestamp": "now"
            }
        })
        
    except WebSocketDisconnect:
        await websocket.close()
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
    
    finally:
        active_websockets.pop(websocket.id, None)


@app.post("/documents/{document_type}/translate", tags=["Documents"])
async def translate_document(document_type: str, request: DocumentOperation, websocket: WebSocket):
    """Translate a document from source language to target language."""
    if document_type not in ["pdf", "docx", "md", "text"]:
        raise HTTPException(400, "Invalid document type")
    
    input_tokens = 0
    output_tokens = 0
    
    try:
        await websocket.accept()
        active_websockets[websocket.id] = websocket
        
        content = request.content or read_file_content(request.file_path)
        if not content:
            raise HTTPException(400, "No content provided")
        
        prompt = create_translate_prompt(content, request.language)
        llm_response = call_llm(prompt, max_tokens=request.max_tokens or MAX_TOKENS)
        
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
        logger.error(f"Error during translation: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
    
    finally:
        active_websockets.pop(websocket.id, None)


@app.post("/documents/{document_type}/extract", tags=["Documents"])
async def extract_from_document(document_type: str, request: DocumentOperation, websocket: WebSocket):
    """Extract specific content from a document."""
    if document_type not in ["pdf", "docx", "md", "text"]:
        raise HTTPException(400, "Invalid document type")
    
    input_tokens = 0
    output_tokens = 0
    
    try:
        await websocket.accept()
        active_websockets[websocket.id] = websocket
        
        content = request.content or read_file_content(request.file_path)
        if not content:
            raise HTTPException(400, "No content provided")
        
        prompt = create_extract_prompt(content, request.prompt)
        llm_response = call_llm(prompt, max_tokens=request.max_tokens or MAX_TOKENS)
        
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
        logger.error(f"Error during extraction: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
    
    finally:
        active_websockets.pop(websocket.id, None)


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
    
    finally:
        active_websockets.pop(websocket.id, None)


@app.get("/stats", tags=["Stats"])
async def get_stats():
    """Get statistics about the backend."""
    try:
        import requests
        test_url = f"http://localhost:{LLAMA_PORT}/v1/models"
        response = requests.get(test_url, timeout=5)
        models = response.json().get("root", {}).get("models", [])
        
        return {
            "status": "success",
            "model_count": len(models),
            "model_path": str(MODEL_PATH),
            "server": f"http://localhost:{LLAMA_PORT}"
        }
    except Exception as e:
        logger.warning(f"Could not fetch stats: {e}")
    return {
        "status": "success",
        "model_path": str(MODEL_PATH)
    }


# Helper functions

def read_file_content(file_path: str) -> str:
    """Read file content."""
    full_path = Path(file_path)
    if not full_path.exists():
        return ""
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_summarize_prompt(content: str, custom_prompt: Optional[str] = None) -> str:
    """Create a prompt for summarizing content."""
    if custom_prompt:
        return f"{custom_prompt}\n\n{content}"
    return f"Please summarize the following text:\n\n{content}"


def create_translate_prompt(content: str, language: str) -> str:
    """Create a prompt for translation."""
    if language:
        return f"Translate the following text to {language}:\n\n{content}"
    return f"Translate the following text:\n\n{content}"


def create_extract_prompt(content: str, prompt: str) -> str:
    """Create a prompt for extracting content."""
    return f"{prompt}\n\n{content}"


def call_llm(prompt: str, max_tokens: int = 2048) -> str:
    """Call llama.cpp via ggc-llama-server or local llama-server."""
    import requests
    
    try:
        test_url = f"http://localhost:{LLAMA_PORT}/v1/chat/completions"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        payload = {
            "model": "qwen-9b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": True
        }
        
        try:
            response = requests.post(test_url, headers=headers, json=payload, timeout=max_tokens + 10)
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data = line_str[6:].strip()
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                full_response += chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            except json.JSONDecodeError:
                                pass
                return full_response
            
        except Exception as e:
            logger.warning(f"llama.cpp server error: {e}, trying local server...")
            local_url = "http://127.0.0.1:11434/v1/chat/completions"
            response = requests.post(local_url, headers=headers, json=payload, timeout=max_tokens + 10)
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data = line_str[6:].strip()
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                full_response += chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            except json.JSONDecodeError:
                                pass
                return full_response
            
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(500, f"Error calling LLM: {str(e)}")
    
    return ""


# Entry point
def main():
    """Main entry point for the backend server."""
    uvicorn.run("server:app", host="0.0.0.0", port=LLAMA_PORT, reload=False, workers=1, log_level="info")


if __name__ == "__main__":
    main()
