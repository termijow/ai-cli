#!/bin/bash

# ==============================================================================
# AI-CLI INDUSTRIAL INSTALLER (Arch Linux + Vulkan Auto-Compile)
# ==============================================================================

PROJECT_ROOT=$(pwd)
BIN_DEST="$HOME/.local/bin"
LLAMA_DIR="$HOME/llama.cpp"
ZSHRC="$HOME/.zshrc"
BASHRC="$HOME/.bashrc"

# Colores
GREEN='\033[0;32m' ; YELLOW='\033[1;33m' ; BLUE='\033[0;34m' ; RED='\033[0;31m' ; NC='\033[0m'

echo -e "${BLUE}🚀 Iniciando Instalador Industrial de AI-CLI...${NC}"

# 1. Sincronización y Dependencias Críticas
echo -e "✦ Sincronizando repositorios y verificando dependencias..."
sudo pacman -Sy --needed --noconfirm \
    jq curl git base-devel cmake vulkan-headers vulkan-icd-loader \
    spirv-headers spirv-tools vulkan-tools lshw

# 2. Detección Inteligente de Hardware
echo -e "✦ Detectando arquitectura de GPU..."
if lspci | grep -qi "VGA.*AMD"; then
    echo -e "  - Detectado: AMD. Instalando vulkan-radeon..."
    sudo pacman -S --needed --noconfirm vulkan-radeon
elif lspci | grep -qi "VGA.*Intel"; then
    echo -e "  - Detectado: Intel. Instalando vulkan-intel..."
    sudo pacman -S --needed --noconfirm vulkan-intel
fi

# 3. Gestión y Compilación de llama.cpp (Vulkan)
if [ ! -d "$LLAMA_DIR" ]; then
    echo -e "✦ Clonando llama.cpp en $LLAMA_DIR..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMA_DIR"
fi

cd "$LLAMA_DIR" || exit 1

# Verificar si el binario existe y tiene soporte Vulkan
NEEDS_COMPILE=true
if [ -f "build/bin/llama-server" ]; then
    if ./build/bin/llama-server --help 2>&1 | grep -qi "vulkan"; then
        echo -e "${GREEN}✅ Binario llama-server con soporte Vulkan detectado.${NC}"
        NEEDS_COMPILE=false
    fi
fi

if [ "$NEEDS_COMPILE" = true ]; then
    echo -e "${YELLOW}✦ Compilando llama.cpp con soporte Vulkan (-DGGML_VULKAN=1)...${NC}"
    rm -rf build
    cmake -B build -DGGML_VULKAN=1
    cmake --build build --config Release -j$(nproc)
    
    if [ -f "build/bin/llama-server" ]; then
        echo -e "${GREEN}✅ Compilación exitosa.${NC}"
    else
        echo -e "${RED}❌ Error crítico en la compilación.${NC}"
        exit 1
    fi
fi

cd "$PROJECT_ROOT" || exit 1

# 4. Configuración de Enlaces y Permisos
echo -e "✦ Configurando binarios globales..."
mkdir -p "$BIN_DEST"
for bin_file in "$PROJECT_ROOT"/bin/*; do
    if [ -f "$bin_file" ]; then
        filename=$(basename "$bin_file")
        chmod +x "$bin_file"
        ln -sf "$bin_file" "$BIN_DEST/$filename"
        echo -e "  - $filename -> $BIN_DEST/"
    fi
done

# 5. Configuración de .env
if [ ! -f ".env" ]; then
    echo -e "✦ Generando configuración .env inicial..."
    cat <<EOF > .env
MODEL_REPO=unsloth/Llama-3.2-3B-Instruct-GGUF
MODEL_FILE=Llama-3.2-3B-Instruct-Q4_K_M.gguf
PORT=8081
LLAMA_PATH=$LLAMA_DIR/build/bin/llama-server
AI_API_URL=http://127.0.0.1:8081/v1/chat/completions
AI_BACKUP_DIR=.ai_backups
EOF
fi

# 6. Actualización de PATH
update_path() {
    local shell_file="$1"
    if [ -f "$shell_file" ]; then
        if ! grep -q "$BIN_DEST" "$shell_file"; then
            echo -e "\n# AI-CLI\nexport PATH=\"\$PATH:$BIN_DEST\"" >> "$shell_file"
            echo "export AI_CLI_ROOT=\"$PROJECT_ROOT\"" >> "$shell_file"
        fi
    fi
}
update_path "$ZSHRC"
update_path "$BASHRC"

echo -e "\n${GREEN}✅ INSTALACIÓN 'PLUG & PLAY' COMPLETADA${NC}"
echo -e "💡 Ejecuta 'source ~/.zshrc' y luego 'ai-serve' para comenzar."
