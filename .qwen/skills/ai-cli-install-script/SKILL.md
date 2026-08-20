---
name: ai-cli-install-script
description: quick-install.sh copies modified scripts without recompiling llama.cpp
source: auto-skill
extracted_at: '2026-08-20T06:35:41.388Z'
---

## Purpose

Create a quick-install script that updates AI-CLI scripts without recompiling llama.cpp.

## Script Content

```bash
#!/bin/bash
# AI-CLI Quick Install Script
# Solo copia scripts modificados, NO compila llama.cpp
# Útil para actualizar cambios en scripts sin recompilar

set -e

# Detectar cambios en scripts y actualizar solo los necesarios
# - ai-pre-launch.sh
# - chat-launcher.sh  
# - chat-history.sh
# - document-editor.html

# Actualizar local server si existe
# - Crear directorio local-server/
# - Copiar local-server.sh

# Actualizar .env con servidor local
# - AI_LOCAL_SERVER=$HOME/.qwen/bin/local-server/local-server.sh
# - AI_EDITOR_SERVER=http://localhost:8080

# Actualizar PATH en zsh/bash
# - export AI_CLI_PATH="$HOME/Documents/ai-cli"
# - export PATH="$AI_CLI_PATH:$PATH"

# Crear alias llama-server
# - alias llama-server="$HOME/Documents/ai-cli/bin/llama-wrapper.sh"
```

## Usage

```bash
chmod +x ~/Documents/ai-cli/quick-install.sh
~/Documents/ai-cli/quick-install.sh
source ~/.zshrc  # O ~/.bashrc
```

## Benefits

- No recompila llama.cpp (ahorro de tiempo)
- Copia solo scripts modificados
- Actualiza configuración de PATH y alias
- Útil para iteraciones rápidas durante desarrollo
