# Roadmap: AI Document Editor + WhatsApp Analyzer

## 📋 Resumen
Este proyecto cuenta con dos suites principales integradas:
1. **AI Document Studio**: Herramienta web local para analizar/editar documentos (Word, PDF, Markdown, Texto) con asistente de IA contextual y generación de documentos Word (.docx).
2. **WhatsApp Analyzer**: Herramienta para analizar conversaciones exportadas, métricas de interacción, extracción de entidades (cumpleaños, direcciones, eventos) y notas de perfil con IA local.
3. **Servicios Unificados**: Control centralizado mediante `ai services` (o `make start-all`).

---

## 🎯 Fase 1: Documentos Básicos (MVP) - ✅ Completado

### 1.1 Infraestructura Local
- [X] **Modelo local configurado** (Qwen3.5 / Gemma en ROCm RX 6600)
- [X] **llama-server** con soporte para *thinking level* y *reasoning budget*
- [X] **Backend API** (FastAPI en puerto `:3094`)
- [X] **Web frontend** (React 19 + Vite en puerto `:5173`)

### 1.2 Soporte de Formatos
- [X] **PDF Parsing** (`pdfplumber` para extracción de texto por páginas y metadatos)
- [X] **Word Processing** (`python-docx` para lectura, extracción de párrafos/tablas y generación en memoria)
- [X] **Markdown** (Soporte nativo y extracción de estructura de encabezados)
- [X] **Plain Text** (Lectura multi-encoding con fallback)

### 1.3 Core Features
- [X] **Editor de Documentos con Asistente Contextual** (Edición en vivo, conteo de palabras, historial y acciones rápidas)
- [X] **Document Operations**:
  - [X] **Resumir**: Resumen ajustable (corto, medio, largo) y multiformato
  - [X] **Corregir / Rephrase**: Mejora de estilo y gramática
  - [X] **Traducir**: Soporte para más de 10 idiomas
  - [X] **Extraer datos**: Entidades, fechas, métricas y datos estructurados

---

## 🎯 Fase 2: WhatsApp Analyzer (Avanzado) - ✅ Completado

### 2.1 WhatsApp Export & Processing
- [X] **Parsing de conversaciones**:
  - [X] Soporte para formatos exportados de Android e iOS (12h y 24h)
  - [X] Soporte para mensajes multilínea
  - [X] Filtrado de mensajes de sistema y multimedia

### 2.2 Extractor de Datos (LLM Local)
- [X] **Estadísticas de Chat**:
  - [X] Conteo de mensajes, palabras, multimedia y ranking de participantes
- [X] **Entity & Relationship Extraction**:
  - [X] Detección de cumpleaños, direcciones, profesiones y notas
  - [X] Detección de tipo de vínculo y tono de conversación
  - [X] Extracción de fechas, eventos y compromisos pendientes

### 2.3 Output & Visualización
- [X] **Dashboard Visual**: Tarjetas de contactos, resumen de vínculo y cronología
- [X] **Exportación**: Descarga directa de reportes estructurados en Markdown

---

## 🛠️ Herramienta Unificada - ✅ Completado

### 3.1 `ai services` Command
- [X] **CLI Orchestrator**:
  - `ai services` (o `ai services start`) → Inicia Backend (:3094) y Frontend (:5173)
  - `ai services stop` → Detiene todos los servicios
  - `ai services restart` → Reinicia los servicios
  - `ai services status` → Estado global del Backend, Frontend y LLM
  - `ai services web` → Abre la interfaz en el navegador
- [X] **Configuración unificada**:
  - `start-all.sh` dinámico sin rutas hardcodeadas
  - `master.py` para gestión de procesos desde Python

---

## 📊 Arquitectura del Sistema
```
┌─────────────────────────────────────────────────────────────┐
│                   ai services / master.py                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
   ┌────────▼─────────┐                  ┌────────▼─────────┐
   │  Frontend (Vite) │                  │ Backend (FastAPI)│
   │   :5173 (React)  │◄── REST / JSON ──┤      :3094       │
   └──────────────────┘                  └────────┬─────────┘
                                                  │
                                                  ▼
                                 ┌──────────────────────────────────┐
                                 │ llama-server (Qwen / ROCm) :1234 │
                                 └──────────────────────────────────┘
```
