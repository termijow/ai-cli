# Roadmap: AI Document Editor + WhatsApp Analyzer

## 📋 Resumen
Este proyecto tiene dos componentes principales:
1. **AI Document Editor**: Tool web local para analizar/editar documentos (Word, PDF, Markdown, Texto) con chat integrado
2. **WhatsApp Analyzer**: Herramienta para analizar conversaciones y extraer datos de relaciones

---

## 🎯 Fase 1: Documentos Básicos (MVP)

### 1.1 Infraestructura Local
- [ ] **Modelo local configurado** (ya hecho: Qwen3.5-9B-GGUF)
- [ ] **llama-server** running (ya configurado en `.env`)
- [ ] **Backend API** (FastAPI con llama.cpp)
- [ ] **Web frontend** (Streamlit o React simple)

### 1.2 Soporte de Formatos
- [ ] **PDF Parsing**
  - [ ] `pdfplumber` o `PyPDF2` para extraer texto
  - [ ] Mantener estructura básica (títulos, párrafos)
  
- [ ] **Word Processing**
  - [ ] `python-docx` para leer/escritor .docx
  - [ ] Extraer títulos, párrafos, tablas
  
- [ ] **Markdown**
  - [ ] `markdown` library (native)
  - [ ] Soporte para encabezados, listas
  
- [ ] **Plain Text**
  - [ ] Soporte nativo (ya disponible)

### 1.3 Core Features
- [ ] **Chat Interface**
  - [ ] Input para documentos (file upload o paste)
  - [ ] Input para prompts ("resúmmelo", "traduce esto", etc.)
  - [ ] Stream de respuestas de llama.cpp
  - [ ] Historial de conversaciones
  
- [ ] **Document Operations**
  - [ ] **Resumir**: Extraer resumen del documento
  - [ ] **Parafrear**: Rephrase texto específico/párrafo
  - [ ] **Modificar**: "Cambia esta sección a otro tono"
  - [ ] **Traducir**: Traducir documento completo o secciones
  - [ ] **Extraer datos**: JSON de información clave

---

## 🎯 Fase 2: WhatsApp Analyzer (Avanzado)

### 2.1 WhatsApp Export & Processing
- [ ] **Exportar conversaciones**
  - [ ] Exportar desde WhatsApp Desktop (JSON/HTML)
  - [ ] O API de Android (adb)
  - [ ] Herramientas existentes: `wa2txt`, `wa2json`
  
- [ ] **Parsing de conversaciones**
  - [ ] Extraer mensajes, fechas, remitentes
  - [ ] Detectar respuestas entre pares
  - [ ] Agrupar por contacto

### 2.2 Extractor de Datos (LLM Local)
- [ ] **Entity Extraction**
  - [ ] Nombres completos
  - [ ] Direcciones
  - [ ] Fechas de cumpleaños
  - [ ] Edades aproximadas
  - [ ] Lugares de encuentro
  - [ ] Eventos importantes
  
- [ ] **Relationship Mapping**
  - [ ] Detección de frecuencia de contacto
  - [ ] Jerarquía de relación (amigo cercano, familiar, etc.)
  - [ ] Historial de interacciones

### 2.3 Output de "Notas"
- [ ] **JSON/Markdown de perfiles**
  - [ ] Nombre: "Juan Pérez"
  - [ ] Dirección: "Calle Falsa 123"
  - [ ] Cumpleaños: "1990-05-15"
  - [ ] Ubicación: "Ciudad de México"
  - [ ] Contacto frecuente: "Semanal"
  - [ ] Notas contextuales
  
- [ ] **Dashboard visual**
  - [ ] Lista de contactos con resumen
  - [ ] Gráfico de frecuencia
  - [ ] Exportable a Markdown/CSV

---

## 🛠️ Herramienta Unificada

### 3.1 `ai services` Command
- [ ] **CLI wrapper** (`ai-services.py`)
  - [ ] `ai services document-editor` → Iniciar web app
  - [ ] `ai services whatsapp-analyzer` → Iniciar analizador
  - [ ] `ai services llm-server` → Verificar estado del modelo
  - [ ] `ai services status` → Estado global del sistema
  
- [ ] **Configuración unificada**
  - [ ] Punto único para `.env`
  - [ ] Logs centralizados
  - [ ] Actualizaciones del modelo

### 3.2 Arquitectura
```
┌─────────────────────────────────────┐
│      ai-services.py (CLI)          │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼─────┐          ┌─────▼────────┐
│ Doc.   │          │  WhatsApp   │
│ Editor │          │  Analyzer   │
│ Stream │          │  CLI/Web    │
└────────┘          └─────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      llama.cpp (Qwen3.5-9B)        │
│      + FastAPI Server               │
└─────────────────────────────────────┘
```

---

## 📊 Cronograma Estimado

| Fase | Duración | Entregables |
|------|----------|-------------|
| **Fase 1** | 2-3 semanas | Web app con PDF/Word, chat básico |
| **Fase 2a** | 1-2 semanas | WhatsApp export + parsing |
| **Fase 2b** | 1-2 semanas | Extractor de datos + notas |
| **Fase 3** | 1 semana | `ai services` CLI unificado |

---

## 🔌 AI CLI - Características Adicionales

### 4.1 AI CLI Features
- [X] **show recents** - Mostrar últimas consultas de la base de datos
- [X] **real-time savings** - Mostrar ahorro acumulado en tiempo real
- [X] **websocket streaming** - soportar streaming de tokens desde llama-server

---

## 📦 Dependencias Principales

```bash
# Backend
fastapi, uvicorn, pydantic

# Documentos
pdfplumber, python-docx, pymupdf (PyMuPDF)

# WhatsApp
wa2json, wa2txt (o scripts personalizados)

# Datos
pandas, sqlalchemy (para guardar notas)

# Frontend (opcional)
streamlit, o React + Vite

# Local LLM
llama-cpp-python, transformers
```

---

## 🚀 Próximos Pasos Inmediatos

1. **Configurar FastAPI backend** con llama.cpp
2. **Probar PDF parsing** básico
3. **Crear Streamlit UI** minimalista
4. **Verificar `ai services` command** funciona

¿Deseas que empecemos con alguna fase en particular?
