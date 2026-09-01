# 🚀 AI-CLI: Tu Agente de Desarrollo Local con TUI y Presets

**AI-CLI** es una herramienta de terminal potente y ligera, inspirada en Gemini CLI, diseñada para permitirte editar, crear y analizar archivos de código utilizando modelos de lenguaje (LLMs) ejecutados **100% localmente** sobre hardware acelerado por GPU (AMD ROCm / Intel Vulkan / CPU).

A diferencia de otras herramientas, AI-CLI se conecta a tu propio servidor de `llama.cpp`, dándote total privacidad, alta velocidad (hasta **60-80 tok/s** en tu GPU AMD RX 6600) y control sobre tu código sin depender de APIs de pago.

---

## ✨ Novedades y Características Principales

*   **🖥️ Panel Interactivo TUI (`ai` / `ai-menu`):** Dashboard centralizado para seleccionar modelos, gestionar el servidor llama.cpp, monitorear uso de VRAM y revisar métricas de ahorro.
*   **🎯 Sistema de Presets por Modelo (`presets/`):**
    *   Guarda configuraciones optimizadas por modelo dentro del propio repositorio (`presets/<modelo>.conf`).
    *   Evita tener que reconfigurar capas GPU, contexto y thinking cada vez que cambias de modelo.
    *   **Qwen 3.5 4B:** Configurado para **60-80 tok/s** (100% en VRAM, KV Cache f16, batch 2048, reasoning off).
    *   **Qwen 3.5 9B:** Balance perfecto para coding y razonamiento (35-45 tok/s, thinking high).
    *   **Qwen 3.6 35B / 27B:** Modo seguro con offload híbrido para evitar saturación de RAM o congelamientos.
*   **💡 Centro de Ayuda Integrado (`ai-help`):** Manual interactivo con guías de rendimiento para ROCm, atajos, flujos de código y troubleshooting.
*   **🧠 Agente de Contexto Inteligente:** Detecta automáticamente archivos relevantes (como `package.json`, `globals.css`, `schema.prisma`, `tailwind.config.ts`).
*   **🎨 Diffs Coloreados Profesionales:** Previsualiza los cambios con colores antes de aplicarlos.
*   **🛡️ Backups Automáticos:** Copia de seguridad en `.ai_backups/` antes de cada modificación.
*   **💸 Alcancía de Ahorros:** Registra tokens y calcula el dinero ahorrado frente a APIs comerciales.

---

## 🛠️ Instalación y Configuración

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/ai-cli.git ~/Documents/ai-cli
   cd ~/Documents/ai-cli
   ```

2. **Ejecuta el instalador (con soporte ROCm para RX 6600):**
   ```bash
   bash install.sh
   ```

3. **Recarga tu shell:**
   ```bash
   source ~/.bashrc  # o source ~/.zshrc
   ```

---

## 🚀 Uso Rápido de Comandos

### 1. Abrir el Panel de Control TUI
Ejecuta `ai` o `ai-menu` sin argumentos para abrir el dashboard interactivo:
```bash
ai
```

### 2. Seleccionar Modelo y Aplicar Preset
Elige entre tus modelos locales con vista previa de hardware y rendimiento:
```bash
ai-models
# o también: ai select
```

### 3. Consultar la Ayuda y Guías
Abre el manual interactivo o consulta un tema específico:
```bash
ai-help
ai help presets
ai help hardware
```

### 4. Iniciar el Servidor
Inicia `llama-server` con el modelo y preset activo:
```bash
ai-serve
# o desde el menú: ai start / ai restart
```

### 5. Modificar o Crear Código
Pide cambios de forma natural. AI-CLI detectará los archivos mencionados:
```bash
ai "añade un botón de login con estilos modernos y validación" app/page.tsx
```

### 6. Historial y Ahorros
```bash
ai-history --limit 10
ai savings
ai stats
```

---

## ⚙️ Presets por Modelo (`presets/`)

Cada modelo cuenta con su propio archivo `.conf` en la carpeta `presets/`:

| Modelo | Preset Recomendado | Capas GPU | Contexto | Thinking / Reasoning | Velocidad Estimada (RX 6600) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3.5-0.8B** | Ultraligero Rápido | 99 (100% VRAM) | 32,768 | `high` / `off` | **120+ tok/s** ⚡ |
| **Qwen3.5-4B** | Velocidad Máxima | 99 (100% VRAM) | 16,384 | `off` | **60-80 tok/s** 🚀 |
| **Qwen3.5-9B** | Equilibrado Coding | 99 (100% VRAM) | 16,384 | `high` | **35-45 tok/s** ⚡ |
| **Qwen3.8-27B** | Híbrido Inteligente | 35 capas | 8,192 | `low` | **18-25 tok/s** |
| **Qwen3.6-35B-A3B** | MoE Híbrido SSM | 28 capas | 40,960 | `high` | **12-15 tok/s** 🧠 |
| **Gemma 4B / 2B**| Fluido 100% VRAM | 99 capas | 8,192 | `off` | **50-100 tok/s** |

Puedes editar cualquier preset desde el menú `ai-models` seleccionando **"Personalizar parámetros y GUARDAR"**.

---

## 📋 Requisitos del Sistema

* **GPU:** AMD Radeon RX 6600 (8GB GDDR6) con ROCm (`hip-runtime-amd`, `rocm-hip-sdk`).
* **Paquetes:** `fzf`, `jq`, `curl`, `sqlite3`, `git`.
* **Motor:** `llama.cpp` compilado con `-DGGML_HIP=ON`.

---

*Potenciado por llama.cpp y ROCm.*
