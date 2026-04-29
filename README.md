# 🚀 AI-CLI: Tu Agente de Desarrollo Local

**AI-CLI** es una herramienta de terminal potente y ligera, inspirada en Gemini CLI, diseñada para permitirte editar, crear y analizar archivos de código utilizando modelos de lenguaje (LLMs) ejecutados **100% localmente**.

A diferencia de otras herramientas, AI-CLI se conecta a tu propio servidor de `llama.cpp`, dándote total privacidad y control sobre tu código sin depender de APIs externas.

---

## ✨ Características Principales

*   **🧠 Agente de Contexto Inteligente:** Detecta automáticamente archivos relevantes (como `globals.css`, `schema.prisma`, `tailwind.config.ts`) basándose en tus instrucciones para dar respuestas precisas.
*   **📂 Mapa del Proyecto:** Envía una estructura simplificada de tu proyecto a la IA para que siempre sepa dónde está trabajando.
*   **🎨 Diffs Coloreados Profesionales:** Previsualiza los cambios con colores (verde para añadidos, rojo para eliminados) antes de aplicarlos, igual que en Git.
*   **🛡️ Seguridad y Estabilidad:**
    *   **Validación Robusta:** Nunca sobreescribe archivos con contenido vacío o errores de la IA.
    *   **Backups Automáticos:** Crea una copia de seguridad en `.ai_backups/` antes de cada modificación.
*   **⚡ Gestión de Servidor con un Comando:** Inicia tu modelo GGUF optimizado con un simple `ai-serve`.
*   **📝 Conventional Commits:** Genera mensajes de commit profesionales basados en tus cambios actuales con `ai commit`.

---

## 🛠️ Instalación

1.  **Clona el repositorio** en tu carpeta de documentos:
    ```bash
    git clone https://github.com/tu-usuario/ai-cli.git ~/Documents/ai-cli
    cd ~/Documents/ai-cli
    ```

2.  **Ejecuta el instalador:**
    ```bash
    bash install.sh
    ```

3.  **Recarga tu terminal:**
    ```bash
    source ~/.bashrc  # o source ~/.zshrc
    ```

---

## 🚀 Uso de Comandos

### 1. Encender el "Cerebro"
Inicia el servidor local de llama.cpp con la configuración optimizada del `.env`:
```bash
ai-serve
```

### 2. Editar o Crear Código
Pide cambios de forma natural. AI-CLI detectará los archivos mencionados:
```bash
ai "añade un botón de login con estilos modernos" app/page.tsx
```
*Si el archivo no existe, AI-CLI creará las carpetas necesarias automáticamente.*

### 3. Mensajes de Commit Inteligentes
Analiza tu `git diff` y genera un commit siguiendo la convención de *Conventional Commits*:
```bash
ai commit
```

---

## ⚙️ Configuración (.env)

El archivo `.env` en la raíz del proyecto controla el comportamiento del agente:

| Variable | Descripción |
| :--- | :--- |
| `MODEL_REPO` | Repositorio de HuggingFace del modelo GGUF. |
| `MODEL_FILE` | Nombre exacto del archivo `.gguf`. |
| `PORT` | Puerto donde correrá el servidor (defecto: 8081). |
| `LLAMA_PATH` | Ruta al binario `llama-server` de tu compilación de llama.cpp. |
| `AI_API_URL` | Endpoint de la API (compatible con OpenAI/llama.cpp). |

---

## 📋 Requisitos

*   [llama.cpp](https://github.com/ggerganov/llama.cpp) (compilado y funcional).
*   `jq`: Para el procesamiento de JSON en la terminal.
*   `curl`: Para la comunicación con la API.
*   **GPU:** Recomendada para una respuesta fluida (flags optimizados para NVIDIA/Apple Silicon incluidos).

---

## 🤝 Contribuir

¡Este es un proyecto Open Source! Si tienes ideas para mejorar el Agente de Contexto o añadir nuevas funciones, siéntete libre de abrir un PR o un Issue.

---

*Inspirado por Gemini CLI. Potenciado por llama.cpp.*
Hola Mundo
