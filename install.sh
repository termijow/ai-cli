#!/bin/bash

# Directorio raíz del proyecto
PROJECT_ROOT=$(pwd)
BIN_DIR="$HOME/.local/bin"

echo "🔧 Instalando AI-CLI..."

# Crear carpeta bin si no existe
mkdir -p "$BIN_DIR"

# Crear enlaces simbólicos usando ln -sf (sobreescribe si ya existe)
ln -sf "$PROJECT_ROOT/bin/ai" "$BIN_DIR/ai"
ln -sf "$PROJECT_ROOT/bin/ai-serve" "$BIN_DIR/ai-serve"

echo "✅ Enlaces simbólicos creados en $BIN_DIR"

# Añadir AI_CLI_ROOT a .zshrc para que los scripts sepan dónde está la raíz y el .env
ZSHRC="$HOME/.zshrc"
if [ -f "$ZSHRC" ]; then
    if ! grep -q "export AI_CLI_ROOT=" "$ZSHRC"; then
        echo -e "\n# AI-CLI Root Directory\nexport AI_CLI_ROOT=\"$PROJECT_ROOT\"" >> "$ZSHRC"
        echo "✅ AI_CLI_ROOT añadido a $ZSHRC"
    else
        # Actualizar la ruta si ya existe por si se movió el repo
        sed -i "s|export AI_CLI_ROOT=.*|export AI_CLI_ROOT=\"$PROJECT_ROOT\"|" "$ZSHRC"
        echo "🔄 AI_CLI_ROOT actualizado en $ZSHRC"
    fi
else
    echo "⚠️ No se encontró .zshrc, asegúrate de añadir export AI_CLI_ROOT=\"$PROJECT_ROOT\" manualmente."
fi

echo "🚀 Instalación completada. Reinicia tu terminal o ejecuta: source ~/.zshrc"
