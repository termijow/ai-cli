#!/bin/bash

# ==============================================================================
# AI-CLI Installer - DevOps Edition v5.1
# ==============================================================================

# Colores para feedback
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 Iniciando instalación de AI-CLI..."

# 1. Obtener ruta absoluta del proyecto
# Forzamos que la ruta sea absoluta y real
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BIN_DIR="$INSTALL_DIR/bin"
BIN_PATH="$BIN_DIR/ai"

# 2. Verificar dependencias
echo "🔍 Verificando dependencias..."
for cmd in curl jq git diff; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} Falta la herramienta: $cmd. Por favor instálala primero."
        exit 1
    fi
done

# 3. Configurar permisos
echo "🔐 Configurando permisos de ejecución..."
chmod +x "$BIN_PATH"
chmod +x "$INSTALL_DIR/lib/core.sh"

# 4. Crear archivo .env si no existe
if [[ ! -f "$INSTALL_DIR/.env" ]]; then
    echo "📄 Creando archivo .env por defecto..."
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
fi

# 5. Agregar al PATH de forma inteligente
SHELL_RC=""
if [[ "$SHELL" == */zsh ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    SHELL_RC="$HOME/.bashrc"
else
    # Fallback a .bashrc si no se detecta
    SHELL_RC="$HOME/.bashrc"
fi

if [[ -f "$SHELL_RC" ]]; then
    if ! grep -q "$BIN_DIR" "$SHELL_RC"; then
        echo "🔗 Agregando AI-CLI al PATH en $SHELL_RC..."
        echo "" >> "$SHELL_RC"
        echo "# AI-CLI PATH" >> "$SHELL_RC"
        echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$SHELL_RC"
        echo -e "${GREEN}[OK]${NC} PATH actualizado."
    else
        echo "✅ AI-CLI ya está en el PATH de $SHELL_RC."
    fi
else
    echo -e "${RED}[WARN]${NC} No se encontró archivo de configuración del Shell ($SHELL_RC). Agrega manualmente $BIN_DIR a tu PATH."
fi

echo "===================================================="
echo -e "${GREEN}¡Instalación de AI-CLI completada!${NC}"
echo "===================================================="
echo "Ruta: $INSTALL_DIR"
echo "1. Reinicia tu terminal o ejecuta: source $SHELL_RC"
echo "2. Configura tu API en $INSTALL_DIR/.env"
echo "3. Prueba el comando: ai commit"
echo "===================================================="
