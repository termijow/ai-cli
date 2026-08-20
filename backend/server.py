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

from fastapi import FastAPI, HTTPException, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Try to import python-docx for Word document generation
try:
    from docx import Document
    from docx.shared import Inches, Pt
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    DOCX_AVAILABLE = False  # Keep for compatibility

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Model configuration
MODEL_PATH = PROJECT_ROOT / "models" / "Qwen3.5-4B-Q4_K_M.gguf"
LLAMA_CPP_SERVER = PROJECT_ROOT / "llama-server"
LLAMA_PORT = os.environ.get("LLAMA_PORT", 1234)
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
    logger.info(f"LLAMA_CPP_SERVER: {LLAMA_CPP_SERVER}")

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


class DocxGenerationRequest(BaseModel):
    """Request for Word document generation."""
    title: Optional[str] = Field(None, description="Document title")
    content: Optional[str] = Field(None, description="Document content")
    prompt: Optional[str] = Field(None, description="Custom prompt for content generation")
    output_path: Optional[str] = Field("/tmp/output.docx", description="Path to save the generated document")
    sections: Optional[List[Dict]] = Field(None, description="List of sections to add (headers, paragraphs)")


class PdfGenerationRequest(BaseModel):
    """Request for PDF document generation."""
    title: Optional[str] = Field(None, description="Document title")
    content: Optional[str] = Field(None, description="Document content")
    prompt: Optional[str] = Field(None, description="Custom prompt for content generation")
    output_path: Optional[str] = Field("/tmp/output.pdf", description="Path to save the generated document")
    format: Optional[str] = Field("markdown", description="Output format: markdown, html, or text")

# Endpoints

@app.on_event("startup")
async def startup_event():
    """Startup event - initialize llama.cpp connection."""
    logger.info("Starting backend server...")
    logger.info(f"Model: {MODEL_PATH}")
    logger.info(f"LLAMA_CPP_SERVER: {LLAMA_CPP_SERVER}")
    
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


@app.post("/stats", tags=["Stats"])
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
            "server": f"http://localhost:{LLAMA_PORT}",
            "features": {
                "word_generation": DOCX_AVAILABLE,
                "pdf_generation": True
            }
        }
    except Exception as e:
        logger.warning(f"Could not fetch stats: {e}")
    return {
        "status": "success",
        "model_path": str(MODEL_PATH),
        "features": {
            "word_generation": DOCX_AVAILABLE,
            "pdf_generation": True
        }
    }


# Document Generation Endpoints

@app.post("/documents/word/generate", tags=["Document Generation"])
async def generate_word_document(request: DocxGenerationRequest):
    """Generate a Word document (.docx) using the LLM."""
    if not DOCX_AVAILABLE:
        raise HTTPException(400, "python-docx is required. Install with: pip install python-docx")
    
    input_tokens = 0
    output_tokens = 0

    try:
        # Generate content using LLM if prompt is provided
        prompt = request.prompt
        content = request.content
        
        if prompt and not content:
            content = call_llm(prompt, max_tokens=2048)
        elif prompt and content:
            content = f"{content}\n\n{call_llm(prompt, max_tokens=2048)}"
        
        if not content:
            raise HTTPException(400, "No content generated")
        
        # Generate the Word document
        doc_bytes = generate_word_document(
            title=request.title or "Documento",
            content=content,
            sections=request.sections
        )
        
        return {
            "status": "success",
            "message": "Document generated successfully",
            "filename": Path(request.output_path or "/tmp/output.docx").name,
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "file_size": len(doc_bytes),
            "tokens_used": {"input": input_tokens, "output": output_tokens}
        }
        
    except ImportError as e:
        raise HTTPException(400, f"Missing dependency: {str(e)}. Install with: pip install python-docx")
    except Exception as e:
        logger.error(f"Error generating Word document: {e}")
        raise HTTPException(500, f"Error generating document: {str(e)}")


@app.post("/documents/pdf/generate", tags=["Document Generation"])
async def generate_pdf_document(request: PdfGenerationRequest):
    """Generate a PDF document from content using the LLM."""
    input_tokens = 0
    output_tokens = 0

    try:
        # Generate content using LLM if prompt is provided
        prompt = request.prompt
        content = request.content
        
        if prompt and not content:
            content = call_llm(prompt, max_tokens=2048)
        elif prompt and content:
            content = f"{content}\n\n{call_llm(prompt, max_tokens=2048)}"
        
        if not content:
            raise HTTPException(400, "No content generated")
        
        # Generate the PDF document
        pdf_bytes = generate_pdf_document(
            title=request.title or "Documento",
            content=content,
            format=request.format or "markdown"
        )
        
        return {
            "status": "success",
            "message": "PDF generated successfully",
            "filename": Path(request.output_path or "/tmp/output.pdf").name,
            "content_type": "application/pdf",
            "file_size": len(pdf_bytes),
            "tokens_used": {"input": input_tokens, "output": output_tokens}
        }
        
    except Exception as e:
        logger.error(f"Error generating PDF document: {e}")
        raise HTTPException(500, f"Error generating document: {str(e)}")


@app.post("/documents/word/generate-interactive", tags=["Document Generation"])
async def generate_word_interactive(websocket: WebSocket):
    """Generate Word document with streaming output."""
    if not DOCX_AVAILABLE:
        raise HTTPException(400, "python-docx is required")
    
    try:
        await websocket.accept()
    except Exception as e:
        logger.error(f"Failed to accept websocket: {e}")
        raise HTTPException(500, f"Failed to accept websocket: {e}")
    
    request = DocxGenerationRequest()
    try:
        # Generate content using LLM
        prompt = request.prompt
        content = request.content
        
        if prompt and not content:
            content = call_llm(prompt, max_tokens=2048)
        
        async def stream_progress():
            """Stream progress to websocket."""
            await websocket.send_json({"type": "progress", "data": {"status": "generating content"}})
            
            # Generate full content
            if prompt and not content:
                content = call_llm(prompt, max_tokens=2048)
                await websocket.send_json({"type": "progress", "data": {"status": "content generated"}})
            
            # Generate document
            doc_bytes = generate_word_document(
                title=request.title or "Documento",
                content=content,
                sections=request.sections
            )
            
            # Stream file progress
            await websocket.send_json({"type": "progress", "data": {"status": "generating document", "size": len(doc_bytes)}})
            
            # Send final result
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "status": "success",
                    "filename": Path(request.output_path or "/tmp/output.docx").name,
                    "file_size": len(doc_bytes),
                    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                }
            })
        
        await stream_progress()
        
    except Exception as e:
        logger.error(f"Error in interactive generation: {e}")
        await websocket.send_json({"type": "error", "data": str(e)})
    finally:
        active_websockets.pop(websocket.id, None)


@app.post("/documents/pdf/generate-interactive", tags=["Document Generation"])
async def generate_pdf_interactive(websocket: WebSocket):
    """Generate PDF document with streaming output."""
    try:
        await websocket.accept()
    except Exception as e:
        logger.error(f"Failed to accept websocket: {e}")
        raise HTTPException(500, f"Failed to accept websocket: {e}")
    
    request = PdfGenerationRequest()
    try:
        # Generate content using LLM
        prompt = request.prompt
        content = request.content
        
        if prompt and not content:
            content = call_llm(prompt, max_tokens=2048)
        
        async def stream_progress():
            """Stream progress to websocket."""
            await websocket.send_json({"type": "progress", "data": {"status": "generating content"}})
            
            # Generate full content
            if prompt and not content:
                content = call_llm(prompt, max_tokens=2048)
                await websocket.send_json({"type": "progress", "data": {"status": "content generated"}})
            
            # Generate PDF
            pdf_bytes = generate_pdf_document(
                title=request.title or "Documento",
                content=content,
                format=request.format or "markdown"
            )
            
            await websocket.send_json({"type": "progress", "data": {"status": "generating document", "size": len(pdf_bytes)}})
            
            await websocket.send_json({
                "type": "complete",
                "data": {
                    "status": "success",
                    "filename": Path(request.output_path or "/tmp/output.pdf").name,
                    "file_size": len(pdf_bytes),
                    "content_type": "application/pdf"
                }
            })
        
        await stream_progress()
        
    except Exception as e:
        logger.error(f"Error in interactive PDF generation: {e}")
        await websocket.send_json({"type": "error", "data": str(e)})
    finally:
        active_websockets.pop(websocket.id, None)


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


def generate_word_document(title: str, content: str, sections: Optional[List[Dict]] = None) -> bytes:
    """Generate a Word document (.docx) from content."""
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx is required for Word document generation. Install with: pip install python-docx")
    
    doc = Document()
    
    # Add title
    doc.add_heading(title, 0)
    
    # Add sections if provided
    if sections:
        for section in sections:
            if section.get("type") == "header":
                doc.add_heading(section.get("text"), section.get("level", 1))
            elif section.get("type") == "paragraph":
                doc.add_paragraph(section.get("text"))
            elif section.get("type") == "table":
                doc.add_table(section.get("columns", 3))
                for row in section.get("rows", []):
                    for cell in row:
                        doc.table.add_row([doc.run(cell)])
    
    # Add main content
    if content:
        for line in content.split('\n'):
            line = line.strip()
            if line:
                doc.add_paragraph(line)
    
    return doc.docx


def generate_pdf_document(title: str, content: str, format: str = "markdown") -> bytes:
    """Generate a PDF document from content.
    
    Since we don't have reportlab installed, we'll convert to Markdown first,
    then use a simple approach to generate PDF using markdown-to-pdf pipeline.
    """
    import subprocess
    import tempfile
    
    # Generate markdown content
    md_content = f"# {title}\n\n{content}\n\n---\n*Generated by AI-CLI*\n"
    
    # Try to use pandoc if available
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            temp_md = f.name
        
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        output_path = output_pdf.name
        
        # Convert markdown to PDF using pandoc
        result = subprocess.run(
            ['pandoc', '-from', 'markdown', '-o', output_path, temp_md],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Read the PDF file
            with open(output_path, 'rb') as f:
                return f.read()
        else:
            return md_content.encode('utf-8')
    
    except FileNotFoundError:
        # pandoc not available, return markdown as fallback
        return md_content.encode('utf-8')
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")


def markdown_to_html(md_content: str) -> str:
    """Convert Markdown to HTML."""
    import re
    
    # Headers
    md_content = re.sub(r'^(#{1,6}) (.+)$', r'<\1>\2\n', md_content, flags=re.MULTILINE)
    
    # Paragraphs
    md_content = re.sub(r'(?m)^(?!<(?:br|em|strong|code|pre|ul|li|ol|dl|dt|dd|div|p|h[1-6]))\s*(.+)$', r'\1', md_content)
    
    # Bold and italic
    md_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md_content)
    md_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md_content)
    
    # Code blocks
    md_content = re.sub(r'```(?:\w+)?\n(.*?)```', r'<pre><code>\n\1\n</code></pre>', md_content, flags=re.DOTALL)
    
    # Inline code
    md_content = re.sub(r'`(.+?)`', r'<code>\1</code>', md_content)
    
    # Links
    md_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', md_content)
    
    # Lists
    md_content = re.sub(r'^[\-\*]\s+(.+)$', r'<li>\1</li>', md_content, flags=re.MULTILINE)
    
    # Newlines to paragraph breaks
    md_content = re.sub(r'(?m)\n\n+', '\n\n', md_content)
    
    return md_content.strip()


def call_llm(prompt: str, max_tokens: int = 2048) -> str:
    """Call remote LLM service on port 1234 (llama.cpp with llama-cpp-python)."""
    import requests

    try:
        test_url = f"http://localhost:1234/v1/completions"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        payload = {
            "model": "localmodel",
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        try:
            response = requests.post(test_url, headers=headers, json=payload, timeout=max_tokens + 10)

            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('text', '') or data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return content

        except Exception as e:
            logger.warning(f"llama.cpp server error: {e}, trying local server...")
            local_url = "http://127.0.0.1:11434/v1/chat/completions"
            response = requests.post(local_url, headers=headers, json=payload, timeout=max_tokens + 10)

            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return content

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(500, f"Error calling LLM: {str(e)}")

    return ""


# Entry point
def main():
    """Main entry point for the backend server."""
    uvicorn.run("server:app", host="0.0.0.0", port=3094, reload=False, workers=1, log_level="info")


if __name__ == "__main__":
    main()
