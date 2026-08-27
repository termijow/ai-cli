#!/usr/bin/env python3
"""
server.py - AI-CLI FastAPI Backend Server
Integrates local llama.cpp instance with Document Parser, WhatsApp Analyzer,
Document Generation (Word/PDF), and REST APIs for the AI-CLI Web UI.
"""

import io
import os
import sys
import json
import sqlite3
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
import requests
import uvicorn

# Setup paths and environment
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from backend.document_parser import DocumentParser, parser
from backend.whatsapp_parser import WhatsAppParser, whatsapp_parser

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ai-cli-backend")

# Try to import python-docx
try:
    import docx
    from docx.shared import Pt, RGBColor, Inches
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Configuration from environment / .env
LLAMA_PORT = int(os.environ.get("LLAMA_PORT", os.environ.get("PORT", 1234)))
LLAMA_HOST = os.environ.get("LLAMA_HOST", "127.0.0.1")
LLAMA_URL = f"http://{LLAMA_HOST}:{LLAMA_PORT}"
LLAMA_TIMEOUT = int(os.environ.get("LLAMA_TIMEOUT", 600))  # Default: 10 minutes (600s)

# Uploads directory
UPLOADS_DIR = PROJECT_ROOT / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or question")
    context: Optional[str] = Field(None, description="Document or selection text context")
    file: Optional[str] = Field(None, description="Optional document context or filename alias")
    system_prompt: Optional[str] = Field(None, description="Optional system instructions")
    max_tokens: Optional[int] = Field(40960, description="Max generation tokens (full context support up to 40k)")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")


class ObsidianExportRequest(BaseModel):
    vault_path: Optional[str] = Field(None, description="Custom Obsidian vault directory path")
    chat_file: Optional[str] = Field(None, description="Specific chat file to export")


class DocumentOperation(BaseModel):
    operation: Optional[str] = Field("process", description="Operation: summarize, translate, extract, rephrase")
    document_type: Optional[str] = Field("text", description="Document type: pdf, docx, md, text")
    content: Optional[str] = Field(None, description="Document raw text content")
    text: Optional[str] = Field(None, description="Alternative text payload")
    file_path: Optional[str] = Field(None, description="Path to file on disk")
    language: Optional[str] = Field(None, description="Target language for translation")
    targetLanguage: Optional[str] = Field(None, description="Target language alias")
    sourceLanguage: Optional[str] = Field(None, description="Source language alias")
    prompt: Optional[str] = Field(None, description="Custom prompt instructions")
    extract_type: Optional[str] = Field(None, description="Extraction mode: entities, dates, numbers, summary")
    type: Optional[str] = Field(None, description="Extraction type alias")
    length: Optional[str] = Field("medium", description="Summary length: short, medium, long")
    format: Optional[str] = Field("text", description="Summary format: text, markdown")
    max_tokens: Optional[int] = Field(2048, description="Maximum tokens")


class DocxGenerationRequest(BaseModel):
    title: Optional[str] = Field("Documento", description="Document title")
    content: Optional[str] = Field("", description="Document body content")
    prompt: Optional[str] = Field(None, description="Optional prompt to generate content via LLM")
    output_path: Optional[str] = Field(None, description="Optional output file path")
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="Optional structured sections")


class PdfGenerationRequest(BaseModel):
    title: Optional[str] = Field("Documento", description="Document title")
    content: Optional[str] = Field("", description="Document content (markdown supported)")
    prompt: Optional[str] = Field(None, description="Optional prompt to generate content via LLM")
    format: Optional[str] = Field("markdown", description="Format: markdown or text")
    output_path: Optional[str] = Field(None, description="Optional output file path")


class WhatsAppAnalyzeRequest(BaseModel):
    chat_text: str = Field(..., description="Raw text exported from WhatsApp")
    prompt_override: Optional[str] = Field(None, description="Optional custom extraction prompt")


# --- Lifespan Context Manager ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 AI-CLI Backend starting up...")
    logger.info(f"LLM Server Target: {LLAMA_URL}")
    yield
    logger.info("🛑 AI-CLI Backend shut down successfully.")


# --- FastAPI Application ---

app = FastAPI(
    title="AI-CLI Backend API",
    description="Unified Backend API for AI Document Processing, WhatsApp Analysis & LLM Services",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- LLM Helper Functions ---

def record_savings(prompt_tokens: int, completion_tokens: int, query_type: str = "web_chat"):
    """Record token usage and savings vs Claude Fable 5 to SQLite and ~/.ai_cli_savings."""
    if prompt_tokens <= 0 and completion_tokens <= 0:
        return
    try:
        # Precios Claude Fable 5: $10/1M input ($0.0000100), $50/1M output ($0.0000500)
        input_cost = prompt_tokens * 0.0000100
        output_cost = completion_tokens * 0.0000500
        total_saving = round(input_cost + output_cost, 4)

        savings_file = Path.home() / ".ai_cli_savings"
        current_savings = 0.0
        if savings_file.exists():
            try:
                current_savings = float(savings_file.read_text().strip())
            except Exception:
                current_savings = 0.0
        new_savings = round(current_savings + total_saving, 2)
        savings_file.write_text(f"{new_savings:.2f}\n")

        db_file = Path.home() / ".ai_cli_db.db"
        if db_file.exists():
            with sqlite3.connect(str(db_file)) as conn:
                conn.execute(
                    "INSERT INTO usage_logs (input_tokens, output_tokens, input_cost, output_savings, total_savings) VALUES (?, ?, ?, ?, ?)",
                    (prompt_tokens, completion_tokens, input_cost, output_cost, new_savings)
                )

        history_dir = Path.home() / ".ai_cli_history"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_file = history_dir / "queries.jsonl"
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query_type": query_type,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "savings": total_saving,
            "total_savings": new_savings
        }
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"No se pudo registrar ahorro: {e}")

def query_llama_cpp(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Call local llama.cpp server OpenAI-compatible chat endpoint.
    Fallback to completions endpoint if chat endpoint is not available.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({"role": "system", "content": "Eres un asistente de IA inteligente, preciso y servicial."})

    messages.append({"role": "user", "content": prompt})

    chat_url = f"{LLAMA_URL}/v1/chat/completions"
    payload = {
        "model": "localmodel",
        "messages": messages,
        "max_tokens": min(max_tokens, 40960),
        "temperature": temperature,
        "stream": False
    }

    try:
        resp = requests.post(chat_url, json=payload, timeout=LLAMA_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tokens_used = prompt_tokens + completion_tokens
            record_savings(prompt_tokens, completion_tokens, query_type="chat")
            return {"content": content, "tokens_used": tokens_used}
    except Exception as e:
        logger.warning(f"Chat completions failed on {chat_url}: {e}, trying completions fallback...")

    # Fallback to /v1/completions
    compl_url = f"{LLAMA_URL}/v1/completions"
    compl_payload = {
        "model": "localmodel",
        "prompt": f"{system_prompt or ''}\n\nUser: {prompt}\n\nAssistant:",
        "max_tokens": min(max_tokens, 40960),
        "temperature": temperature
    }
    try:
        resp = requests.post(compl_url, json=compl_payload, timeout=LLAMA_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("text", "")
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tokens_used = prompt_tokens + completion_tokens
            record_savings(prompt_tokens, completion_tokens, query_type="chat")
            return {"content": content, "tokens_used": tokens_used}
    except Exception as e:
        logger.error(f"Completions fallback failed on {compl_url}: {e}")

    # Return mock or offline message if LLM is not responding
    return {
        "content": "⚠️ No se pudo comunicar con el servidor de LLM (llama-server). Verifica que esté iniciado en el puerto 1234 con 'ai serve' o 'ai services start'.",
        "tokens_used": 0
    }


def create_docx_bytes(title: str, content: str, sections: Optional[List[Dict[str, Any]]] = None) -> bytes:
    """Create DOCX bytes in memory safely using python-docx with strict Arial 18/16/14/12 typography in black (#000000)."""
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx no está instalado. Instala con: pip install python-docx")

    import re
    doc = docx.Document()

    # Configure 1 inch margins
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)

    # Style: Normal
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Arial'
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = RGBColor(0, 0, 0)
    style_normal.font.bold = False

    lines = content.splitlines() if content else []

    if sections:
        for section in sections:
            sec_title = section.get("title") or section.get("header")
            if sec_title:
                p = doc.add_paragraph()
                run = p.add_run(sec_title)
                run.font.name = 'Arial'
                run.font.size = Pt(16)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 0, 0)
            sec_content = section.get("content") or section.get("text", "")
            if sec_content:
                for line in str(sec_content).splitlines():
                    if line.strip():
                        p = doc.add_paragraph()
                        run = p.add_run(line.strip())
                        run.font.name = 'Arial'
                        run.font.size = Pt(12)
                        run.font.bold = False
                        run.font.color.rgb = RGBColor(0, 0, 0)

    # Parse content line by line (including Markdown tables)
    is_first_line = True
    i = 0
    while i < len(lines):
        raw_line = lines[i].strip()
        if not raw_line:
            i += 1
            continue

        # Ignore dummy "Documento_1" / "Documento_2" line
        if re.match(r"^Documento_\d+$", raw_line, re.IGNORECASE):
            i += 1
            continue

        # Page break
        if raw_line in ("---", "***", "___", "[Salto de página]", "[Salto de pagina]"):
            doc.add_page_break()
            i += 1
            continue

        # Markdown Table Detection (| Header 1 | Header 2 |)
        if raw_line.startswith("|") and raw_line.endswith("|") and raw_line.count("|") >= 2:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            # Parse table rows
            table_rows = []
            for t_line in table_lines:
                # Skip separator lines like |---|---|
                if re.match(r"^\|(\s*:?-+:?\s*\|)+$", t_line):
                    continue
                cells = [c.strip() for c in t_line.strip("|").split("|")]
                if any(cells):
                    table_rows.append(cells)

            if table_rows:
                num_cols = max(len(r) for r in table_rows)
                for r in table_rows:
                    while len(r) < num_cols:
                        r.append("")

                table = doc.add_table(rows=len(table_rows), cols=num_cols)
                table.style = 'Table Grid'
                for r_idx, row_data in enumerate(table_rows):
                    for c_idx, cell_value in enumerate(row_data):
                        cell = table.cell(r_idx, c_idx)
                        cell.text = cell_value
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.font.name = 'Arial'
                                run.font.size = Pt(11)
                                run.font.bold = (r_idx == 0)
                                run.font.color.rgb = RGBColor(0, 0, 0)
            continue

        # H1 (# Title)
        if raw_line.startswith("# ") and not raw_line.startswith("## "):
            text = raw_line[2:].strip()
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.name = 'Arial'
            run.font.size = Pt(18)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
        # H2 (## Title or 1. Section, 2. Section)
        elif (raw_line.startswith("## ") and not raw_line.startswith("### ")) or re.match(r"^\d+\.\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]", raw_line):
            text = raw_line[3:].strip() if raw_line.startswith("## ") else raw_line
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.name = 'Arial'
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
        # H3 (### Title or 1.1. Subsection, 2.1. Subsection)
        elif raw_line.startswith("### ") or re.match(r"^\d+\.\d+\.?\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]", raw_line):
            text = raw_line[4:].strip() if raw_line.startswith("### ") else raw_line
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.name = 'Arial'
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
        # Bullet list
        elif re.match(r"^[-*•]\s+", raw_line):
            text = re.sub(r"^[-*•]\s+", "", raw_line)
            p = doc.add_paragraph(style='List Bullet')
            run = p.add_run(text)
            run.font.name = 'Arial'
            run.font.size = Pt(12)
            run.font.bold = False
            run.font.color.rgb = RGBColor(0, 0, 0)
        # First non-header line that acts as main title
        elif is_first_line and len(raw_line) < 120 and not raw_line.endswith('.'):
            p = doc.add_paragraph()
            run = p.add_run(raw_line)
            run.font.name = 'Arial'
            run.font.size = Pt(18)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
        # Normal paragraph
        else:
            p = doc.add_paragraph()
            run = p.add_run(raw_line)
            run.font.name = 'Arial'
            run.font.size = Pt(12)
            run.font.bold = False
            run.font.color.rgb = RGBColor(0, 0, 0)

        is_first_line = False
        i += 1

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# --- API Routes ---

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-cli-backend",
        "version": "1.0.0",
        "llama_url": LLAMA_URL
    }


@app.get("/model/info", tags=["Model"])
async def get_model_info():
    """Check connection to llama-server and get model metadata."""
    is_online = False
    model_name = os.environ.get("MODEL_FILE", "Qwen3.5-9B-GGUF")
    try:
        resp = requests.get(f"{LLAMA_URL}/v1/models", timeout=3)
        if resp.status_code == 200:
            is_online = True
            models_data = resp.json().get("data", resp.json().get("models", []))
            if models_data and isinstance(models_data, list):
                model_name = models_data[0].get("id", model_name)
    except Exception:
        is_online = False

    return {
        "status": "online" if is_online else "offline",
        "model": model_name,
        "server_url": LLAMA_URL,
        "port": LLAMA_PORT,
        "features": {
            "docx_generation": DOCX_AVAILABLE,
            "pdf_parsing": True,
            "whatsapp_analysis": True,
            "multi_format_parser": True
        }
    }


@app.post("/chat", tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """Chat with the local LLM with full context up to 40k tokens and auto-compaction."""
    ctx = (request.context or request.file or "").strip()

    # Intelligent compaction if context exceeds 160,000 characters (~40k tokens)
    if len(ctx) > 160000:
        logger.info(f"Context size ({len(ctx)} chars, ~{len(ctx)//4} tokens) exceeds 40k threshold. Applying auto-compaction.")
        ctx = ctx[:80000] + "\n\n[... CONTENIDO INTERMEDIO COMPACTADO AUTOMÁTICAMENTE (>40K TOKENS) ...]\n\n" + ctx[-70000:]

    if ctx:
        full_prompt = f"=== CONTEXTO DEL DOCUMENTO O SELECCIÓN ===\n{ctx}\n\n=== INSTRUCCIÓN DEL USUARIO ===\n{request.message}"
    else:
        full_prompt = request.message

    max_tokens = request.max_tokens or 40960

    llm_res = query_llama_cpp(
        prompt=full_prompt,
        system_prompt=request.system_prompt or "Eres un editor y redactor profesional de documentos.",
        max_tokens=max_tokens,
        temperature=request.temperature or 0.7
    )

    return {
        "content": llm_res["content"],
        "response": llm_res["content"],
        "tokens_used": llm_res["tokens_used"]
    }


@app.post("/documents/parse", tags=["Documents"])
async def parse_document_endpoint(
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None)
):
    """
    Parse an uploaded file or existing text into clean string content with metadata.
    """
    if file:
        file_ext = Path(file.filename).suffix.lower()
        temp_dest = UPLOADS_DIR / file.filename
        file_bytes = await file.read()
        with open(temp_dest, "wb") as f:
            f.write(file_bytes)

        result = parser.parse(str(temp_dest), document_type=file_ext)
        return {
            "success": result.success,
            "filename": file.filename,
            "content": result.content,
            "metadata": result.metadata,
            "error": result.error
        }

    if file_path:
        result = parser.parse(file_path, document_type=document_type)
        return {
            "success": result.success,
            "filename": Path(file_path).name,
            "content": result.content,
            "metadata": result.metadata,
            "error": result.error
        }

    if content:
        result = parser.parse_content(content, document_type=document_type or "text")
        return {
            "success": True,
            "filename": "document.txt",
            "content": result.content,
            "metadata": result.metadata,
            "error": None
        }

    raise HTTPException(status_code=400, detail="Debes proporcionar un archivo, una ruta (file_path) o contenido (content).")


@app.post("/documents/{document_type}/summarize", tags=["Documents"])
async def summarize_document(document_type: str, request: DocumentOperation):
    """Summarize document content or file."""
    text_content = request.content or request.text or ""
    if not text_content and request.file_path:
        parse_res = parser.parse(request.file_path, document_type=document_type)
        text_content = parse_res.content

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="No se proporcionó contenido para resumir.")

    len_desc = {
        "short": "un resumen breve y conciso en 2-3 oraciones o puntos clave",
        "medium": "un resumen equilibrado destacando los puntos principales y conclusiones",
        "long": "un resumen detallado y exhaustivo que cubra todas las secciones importantes"
    }.get(request.length, "un resumen claro y bien estructurado")

    format_desc = "en formato Markdown con viñetas y títulos claros" if request.format == "markdown" else "en texto fluido"

    prompt = f"""Genera {len_desc} del siguiente documento {format_desc}.
{request.prompt or ''}

DOCUMENTO:
{text_content}"""

    llm_res = query_llama_cpp(prompt, max_tokens=request.max_tokens or 2048)
    return {
        "status": "success",
        "summary": llm_res["content"],
        "result": llm_res["content"],
        "tokens_used": llm_res["tokens_used"]
    }


@app.post("/documents/{document_type}/translate", tags=["Documents"])
async def translate_document(document_type: str, request: DocumentOperation):
    """Translate text content to target language."""
    text_content = request.content or request.text or ""
    if not text_content and request.file_path:
        parse_res = parser.parse(request.file_path, document_type=document_type)
        text_content = parse_res.content

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="No se proporcionó texto para traducir.")

    target_lang = request.language or request.targetLanguage or "español"
    prompt = f"""Traduce de forma fluida, natural y precisa el siguiente texto al idioma: {target_lang}.
Mantén el formato original del documento.

TEXTO ORIGINAL:
{text_content}

TRADUCCIÓN:"""

    llm_res = query_llama_cpp(prompt, max_tokens=request.max_tokens or 2048)
    return {
        "status": "success",
        "translatedText": llm_res["content"],
        "result": llm_res["content"],
        "target_language": target_lang,
        "tokens_used": llm_res["tokens_used"]
    }


@app.post("/documents/{document_type}/extract", tags=["Documents"])
async def extract_information(document_type: str, request: DocumentOperation):
    """Extract key facts, entities, dates, or custom structured data from document."""
    text_content = request.content or request.text or ""
    if not text_content and request.file_path:
        parse_res = parser.parse(request.file_path, document_type=document_type)
        text_content = parse_res.content

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="No se proporcionó contenido para extraer información.")

    ext_type = request.extract_type or request.type or "entities"
    instructions = {
        "entities": "Extrae todas las entidades clave (Personas, Organizaciones, Lugares, Productos, Tecnologías) en formato JSON.",
        "dates": "Extrae todas las fechas, plazos, cronogramas y momentos temporales mencionados en formato JSON con su contexto.",
        "numbers": "Extrae todas las métricas, cantidades, precios, porcentajes y cifras numéricas en formato JSON.",
        "summary": "Extrae los 5 puntos clave e insights fundamentales del documento."
    }.get(ext_type, request.prompt or "Extrae la información más relevante en formato JSON estructurado.")

    prompt = f"""{instructions}

DOCUMENTO:
{text_content}

Responde con la información organizada y clara."""

    llm_res = query_llama_cpp(prompt, max_tokens=request.max_tokens or 2048)
    return {
        "status": "success",
        "extractedData": llm_res["content"],
        "result": llm_res["content"],
        "tokens_used": llm_res["tokens_used"]
    }


@app.post("/documents/word/generate", tags=["Document Generation"])
async def generate_word_document_api(request: DocxGenerationRequest):
    """Generate Word (.docx) document using LLM or structured sections."""
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=400, detail="python-docx no está disponible. Instálalo con: pip install python-docx")

    content = request.content or ""
    tokens_used = 0

    if request.prompt and not content:
        llm_res = query_llama_cpp(
            prompt=f"Escribe el contenido completo y bien estructurado para un documento titulado '{request.title}'.\nInstrucciones: {request.prompt}",
            max_tokens=3000
        )
        content = llm_res["content"]
        tokens_used = llm_res["tokens_used"]

    try:
        doc_bytes = create_docx_bytes(
            title=request.title or "Documento Generado",
            content=content,
            sections=request.sections
        )

        filename = f"{Path(request.title or 'documento').stem}.docx"

        if request.output_path:
            out_file = Path(request.output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "wb") as f:
                f.write(doc_bytes)

        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"Error generating DOCX: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar documento Word: {str(e)}")


@app.post("/documents/pdf/generate", tags=["Document Generation"])
async def generate_pdf_document_api(request: PdfGenerationRequest):
    """Generate Markdown/PDF document."""
    content = request.content or ""
    tokens_used = 0

    if request.prompt and not content:
        llm_res = query_llama_cpp(
            prompt=f"Escribe un documento profesional en formato Markdown titulado '{request.title}'.\nInstrucciones: {request.prompt}",
            max_tokens=3000
        )
        content = llm_res["content"]
        tokens_used = llm_res["tokens_used"]

    full_md = f"# {request.title or 'Documento'}\n\n{content}\n\n---\n*Generado localmente con AI-CLI*"
    return {
        "status": "success",
        "title": request.title,
        "content": full_md,
        "tokens_used": tokens_used
    }


@app.post("/whatsapp/parse", tags=["WhatsApp"])
async def parse_whatsapp_chat(request: WhatsAppAnalyzeRequest):
    """Parse WhatsApp exported chat transcript into statistics and structured message log."""
    if not request.chat_text.strip():
        raise HTTPException(status_code=400, detail="El texto del chat de WhatsApp está vacío.")

    stats = whatsapp_parser.parse_text(request.chat_text)
    return {
        "status": "success",
        "stats": stats
    }


@app.post("/whatsapp/analyze", tags=["WhatsApp"])
async def analyze_whatsapp_chat(request: WhatsAppAnalyzeRequest):
    """
    Perform deep relationship analysis and entity extraction on WhatsApp chat using local LLM.
    """
    if not request.chat_text.strip():
        raise HTTPException(status_code=400, detail="El texto del chat de WhatsApp está vacío.")

    stats = whatsapp_parser.parse_text(request.chat_text)
    prompt = request.prompt_override or whatsapp_parser.build_analysis_prompt(stats)

    llm_res = query_llama_cpp(
        prompt=prompt,
        system_prompt="Eres un analista de relaciones y extractor de datos estructurados especializado en transcripciones de mensajería.",
        max_tokens=3000,
        temperature=0.3
    )

    return {
        "status": "success",
        "stats": stats,
        "analysis_raw": llm_res["content"],
        "tokens_used": llm_res["tokens_used"]
    }


@app.post("/whatsapp/analyze-stream", tags=["WhatsApp"])
async def analyze_whatsapp_stream_endpoint(request: WhatsAppAnalyzeRequest):
    """
    Stream real-time batch processing progress and accumulated entity extraction via Server-Sent Events (SSE).
    """
    if not request.chat_text.strip():
        raise HTTPException(status_code=400, detail="El texto del chat de WhatsApp está vacío.")

    from backend.whatsapp_analyzer_engine import LargeChatAnalyzer
    engine = LargeChatAnalyzer(chunk_size_messages=150)

    def query_fn(prompt: str):
        return query_llama_cpp(prompt, max_tokens=1500, temperature=0.2)

    async def event_generator():
        try:
            async for event in engine.analyze_chat_stream(request.chat_text, query_fn):
                payload = json.dumps(event, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except Exception as e:
            err_payload = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"data: {err_payload}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/whatsapp/dossiers", tags=["WhatsApp"])
async def list_whatsapp_dossiers():
    """List all saved dossiers and profiles in ~/.ai_cli_whatsapp."""
    from backend.whatsapp_analyzer_engine import STORAGE_DIR
    dossiers = []
    if STORAGE_DIR.exists():
        for f in STORAGE_DIR.glob("*_dossier.md"):
            stat = f.stat()
            json_path = f.parent / f"{f.stem.replace('_dossier', '_profile')}.json"
            dossiers.append({
                "id": f.stem,
                "title": f.stem.replace("_dossier", "").replace("_", " ").title(),
                "file_md": f.name,
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
                "has_json": json_path.exists()
            })
    return {"status": "success", "dossiers": dossiers}


@app.get("/whatsapp/dossiers/{filename}", tags=["WhatsApp"])
async def get_whatsapp_dossier_content(filename: str):
    """Get the markdown content of a saved dossier."""
    from backend.whatsapp_analyzer_engine import STORAGE_DIR
    safe_name = Path(filename).name
    file_path = STORAGE_DIR / safe_name
    if not file_path.exists():
        file_path = STORAGE_DIR / f"{safe_name}_dossier.md"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dossier no encontrado.")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {"status": "success", "filename": file_path.name, "content": content}


@app.post("/whatsapp/export-obsidian", tags=["WhatsApp", "Obsidian"])
async def export_to_obsidian_vault(request: Optional[ObsidianExportRequest] = None):
    """Export parsed WhatsApp profiles and dossiers into an Obsidian Vault CRM."""
    from backend.obsidian_vault_exporter import ObsidianVaultExporter
    from backend.whatsapp_analyzer_engine import STORAGE_DIR

    custom_vault = Path(request.vault_path) if request and request.vault_path else None
    exporter = ObsidianVaultExporter(vault_path=custom_vault)

    # Load all saved json profiles from STORAGE_DIR
    json_files = list(STORAGE_DIR.glob("*_profile.json"))
    if not json_files:
        raise HTTPException(status_code=400, detail="No hay perfiles de WhatsApp analizados todavía. Analiza una conversación primero.")

    all_contacts = []
    total_events = 0

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
            res = exporter.export_profile(profile_data)
            all_contacts.extend(res.get("contacts_exported", []))
            total_events += res.get("events_exported", 0)
        except Exception as e:
            logger.error(f"Error exporting {jf.name} to Obsidian: {e}")

    return {
        "status": "success",
        "vault_path": str(exporter.vault_path),
        "total_contacts": len(set(all_contacts)),
        "contacts": list(set(all_contacts)),
        "events_count": total_events,
        "message": f"✓ Base de datos sincronizada con Obsidian en {exporter.vault_path}"
    }


@app.get("/whatsapp/obsidian-status", tags=["WhatsApp", "Obsidian"])
async def get_obsidian_status():
    """Get status of the WhatsApp Obsidian Vault."""
    from backend.obsidian_vault_exporter import vault_exporter
    return vault_exporter.get_status()


@app.get("/documents/list", tags=["Documents"])
async def list_uploaded_documents():
    """List uploaded and cached documents available for processing."""
    docs = []
    if UPLOADS_DIR.exists():
        for f in UPLOADS_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in [".txt", ".md", ".pdf", ".docx"]:
                stat = f.stat()
                docs.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "type": f.suffix.lower().lstrip("."),
                    "modified": stat.st_mtime
                })
    return {"status": "success", "documents": docs}


# --- Server Runner ---

def main():
    port = int(os.environ.get("BACKEND_PORT", 3094))
    host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    logger.info(f"Starting uvicorn server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
