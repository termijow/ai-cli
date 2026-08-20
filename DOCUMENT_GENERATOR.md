# AI CLI Document Generator

## Document Generation System

AI-CLI ahora incluye la capacidad de generar documentos Word (.docx) y PDF (.pdf) utilizando tu modelo local.

### Características

- **Generación de contenido con LLM**: El modelo genera el contenido del documento basado en tu prompt
- **Formato Word (.docx)**: Generación de documentos Word completos con estilos y secciones
- **Formato PDF**: Conversión de Markdown a PDF
- **Streaming**: Soporte para streaming de progreso para una experiencia mejorada
- **100% Local**: Todo el procesamiento se realiza en tu máquina, sin enviar datos a la nube

### API Endpoints

#### Word Document Generation

**Endpoint:** `POST /documents/word/generate`

**Request Body:**
```json
{
  "prompt": "Crea un documento de introducción a Python con ejemplos básicos",
  "title": "Introducción a Python",
  "output_path": "/path/to/output.docx",
  "sections": [
    {
      "title": "Introducción",
      "content": "Python es un lenguaje de programación..."
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Document generated successfully",
  "filename": "output.docx",
  "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": 12345,
  "tokens_used": {"input": 10, "output": 500}
}
```

**Streaming Endpoint:** `POST /documents/word/generate-interactive`

Utiliza WebSocket para recibir el progreso de generación en tiempo real.

#### PDF Document Generation

**Endpoint:** `POST /documents/pdf/generate`

**Request Body:**
```json
{
  "prompt": "Crea un informe de ventas con estadísticas mensuales",
  "title": "Informe de Ventas",
  "output_path": "/path/to/output.pdf",
  "format": "markdown",
  "content": "# Informe de Ventas\n\n## Resumen\n\nLas ventas del mes han sido..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "PDF generated successfully",
  "filename": "output.pdf",
  "content_type": "application/pdf",
  "file_size": 45678,
  "tokens_used": {"input": 10, "output": 500}
}
```

**Streaming Endpoint:** `POST /documents/pdf/generate-interactive`

Utiliza WebSocket para recibir el progreso de generación en tiempo real.

### Uso con curl

#### Generar documento Word

```bash
curl -X POST http://localhost:3094/documents/word/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Crea un informe de ventas para el Q1 2024",
    "title": "Informe de Ventas Q1 2024"
  }'
```

#### Generar documento PDF

```bash
curl -X POST http://localhost:3094/documents/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Crea una presentación de marketing para un nuevo producto",
    "title": "Marketing Presentation",
    "content": "# Presentación de Marketing\n\n## Objetivos\n- Aumentar la visibilidad del producto\n- Generar leads potenciales..."
  }'
```

### Instalación de Dependencias

Para usar las funciones de generación de documentos, instala las dependencias necesarias:

```bash
pip install python-docx pandoc
```

### Ejemplo de Flujo Completo

1. **Configura tu modelo** usando `ai` o `ai-models`
2. **Inicia el servidor** con `ai-serve`
3. **Genera un documento** usando los endpoints API

```bash
# 1. Configura modelo
ai select

# 2. Inicia servidor
ai-serve

# 3. Genera documento Word
curl -X POST http://localhost:3094/documents/word/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Crea un documento de requerimientos para una aplicación web",
    "title": "Requerimientos de Aplicación Web"
  }'
```

### Integración con AI-CLI

El sistema está diseñado para integrarse fácilmente con el panel TUI de AI-CLI, permitiendo:

- Generar documentos directamente desde el terminal
- Visualizar el progreso en tiempo real
- Descargar los documentos generados
- Incluir métricas de uso de tokens

---

**Powered by llama.cpp y python-docx**
