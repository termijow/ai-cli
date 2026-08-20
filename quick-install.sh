#!/bin/bash
# AI-CLI Quick Install Script
# Solo copia scripts modificados, NO compila llama.cpp
# Útil para actualizar cambios en scripts sin recompilar

set -e

echo "🔧 AI-CLI Quick Install Script"
echo ""

# Crear directorio .qwen/bin si no existe
mkdir -p "$HOME/.qwen/bin"

# Detectar si hay cambios en los scripts y actualizar solo los necesarios
if [[ -f "$HOME/Documents/ai-cli/bin/ai-pre-launch.sh" ]]; then
    if [[ ! -x "$HOME/.qwen/bin/ai-pre-launch.sh" ]] || [[ ! -f "$HOME/.qwen/bin/ai-pre-launch.sh" ]]; then
        echo "📄 Actualizando ai-pre-launch.sh..."
        cp "$HOME/Documents/ai-cli/bin/ai-pre-launch.sh" "$HOME/.qwen/bin/"
        chmod +x "$HOME/.qwen/bin/ai-pre-launch.sh"
    fi
fi

if [[ -f "$HOME/Documents/ai-cli/bin/chat-launcher.sh" ]]; then
    if [[ ! -x "$HOME/.qwen/bin/chat-launcher.sh" ]] || [[ ! -f "$HOME/.qwen/bin/chat-launcher.sh" ]]; then
        echo "📄 Actualizando chat-launcher.sh..."
        cp "$HOME/Documents/ai-cli/bin/chat-launcher.sh" "$HOME/.qwen/bin/"
        chmod +x "$HOME/.qwen/bin/chat-launcher.sh"
    fi
fi

if [[ -f "$HOME/Documents/ai-cli/bin/chat-history.sh" ]]; then
    if [[ ! -x "$HOME/.qwen/bin/chat-history.sh" ]] || [[ ! -f "$HOME/.qwen/bin/chat-history.sh" ]]; then
        echo "📄 Actualizando chat-history.sh..."
        cp "$HOME/Documents/ai-cli/bin/chat-history.sh" "$HOME/.qwen/bin/"
        chmod +x "$HOME/.qwen/bin/chat-history.sh"
    fi
fi

if [[ -f "$HOME/Documents/ai-cli/bin/document-editor.html" ]]; then
    if [[ ! -x "$HOME/.qwen/bin/document-editor.html" ]] || [[ ! -f "$HOME/.qwen/bin/document-editor.html" ]]; then
        echo "📄 Actualizando document-editor.html..."
        cp "$HOME/Documents/ai-cli/bin/document-editor.html" "$HOME/.qwen/bin/"
        chmod +x "$HOME/.qwen/bin/document-editor.html"
    fi
fi

# Actualizar local server si existe
if [[ -f "$HOME/Documents/ai-cli/bin/local-server/local-server.sh" ]]; then
    if [[ ! -f "$HOME/.qwen/bin/local-server/local-server.sh" ]]; then
        echo "📄 Creando local-server..."
        mkdir -p "$HOME/.qwen/bin/local-server"
        cat > "$HOME/.qwen/bin/local-server/local-server.sh" << 'EOF'
#!/bin/bash
# AI-CLI Local Server
# Serve document editor

cd "$(dirname "$0")"
python3 -m http.server 8080
EOF
        chmod +x "$HOME/.qwen/bin/local-server/local-server.sh"
    fi
fi

# Actualizar .env con el servidor local
if ! grep -q "AI_LOCAL_SERVER" ~/.env 2>/dev/null; then
    echo "📄 Actualizando .env..."
    cat >> ~/.env << EOF
# AI-CLI Local Server
AI_LOCAL_SERVER=$HOME/.qwen/bin/local-server/local-server.sh
AI_EDITOR_SERVER=http://localhost:8080
EOF
fi

# Actualizar PATH en zsh/bash si es necesario
update_shell() {
    local shell_file="$1"
    if [[ -f "$shell_file" ]]; then
        if ! grep -q "AI_CLI_PATH" "$shell_file" 2>/dev/null; then
            echo "📄 Actualizando $shell_file..."
            echo 'export AI_CLI_PATH="$HOME/Documents/ai-cli"' >> "$shell_file"
            echo 'export PATH="$AI_CLI_PATH:$PATH"' >> "$shell_file"
        fi
    fi
}

update_shell "$HOME/.zshrc" 2>/dev/null || true
update_shell "$HOME/.bashrc" 2>/dev/null || true

# Crear alias para llama.cpp que incluya el hook
if [[ ! -f "$HOME/.zshrc" ]] && [[ -d "$HOME/.zsh" ]]; then
    if ! grep -q "alias llama-server" "$HOME/.zshrc" 2>/dev/null; then
        echo "📄 Creando alias llama-server en .zshrc..."
        echo 'alias llama-server="$HOME/Documents/ai-cli/bin/llama-wrapper.sh"' >> "$HOME/.zshrc"
    fi
fi

if [[ ! -f "$HOME/.bashrc" ]]; then
    if ! grep -q "alias llama-server" "$HOME/.bashrc" 2>/dev/null; then
        echo "📄 Creando alias llama-server en .bashrc..."
        echo 'alias llama-server="$HOME/Documents/ai-cli/bin/llama-wrapper.sh"' >> "$HOME/.bashrc"
    fi
fi

echo ""
echo "✅ AI-CLI instalado y actualizado correctamente!"
echo ""
echo "📌 Comandos útiles:"
echo "  • source ~/.zshrc          # Cargar configuración"
echo "  • ai models                # Listar modelos"
echo "  • ai savings               # Ver ahorro acumulado"
echo "  • document-editor          # Abrir editor de documentos"
echo "  • llama-server <modelo>    # Cargar modelo con hooks"
