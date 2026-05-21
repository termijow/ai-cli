#!/bin/bash

# ==============================================================================
# AI-CLI HARDWARE CONFIGURATION ASSISTANT (Arch Linux)
# ==============================================================================

PROJECT_ROOT=$(pwd)
BIN_DEST="$HOME/.local/bin"
LLAMA_DIR="$HOME/llama.cpp"
ZSHRC="$HOME/.zshrc"
BASHRC="$HOME/.bashrc"

# Colores
GREEN='\033[0;32m' ; YELLOW='\033[1;33m' ; BLUE='\033[0;34m' ; RED='\033[0;31m' ; NC='\033[0m'

clear
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 ASISTENTE DE CONFIGURACIÓN DE HARDWARE AI-CLI${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. Sincronización Inicial
echo -e "\n✦ Sincronizando bases de datos de pacman..."
sudo pacman -Sy

# 2. Selección de Hardware
echo -e "\n¿Qué hardware deseas configurar para la aceleración?"
echo -e "1) ${GREEN}AMD ROCm${NC} (Escritorio RX 6600 / Alto Rendimiento)"
echo -e "2) ${BLUE}Intel Vulkan${NC} (Laptop i5 / Gráficos Integrados)"
echo -e "3) ${YELLOW}Solo CPU${NC} (Sin aceleración de GPU)"
echo -e "4) Salir"

read -p "Elija una opción [1-4]: " hw_option

case $hw_option in
    1)
        AI_MODE="AMD"
        echo -e "\n✦ Instalando dependencias para AMD ROCm..."
        sudo pacman -S --needed --noconfirm jq curl git base-devel cmake \
            rocm-hip-sdk hip-runtime-amd vulkan-radeon vulkan-headers
        CMAKE_FLAGS="-DGGML_HIPBLAS=1 -DAMDGPU_TARGETS=gfx1032"
        ;;
    2)
        AI_MODE="INTEL"
        echo -e "\n✦ Instalando dependencias para Intel Vulkan..."
        sudo pacman -S --needed --noconfirm jq curl git base-devel cmake \
            vulkan-intel vulkan-headers spirv-headers spirv-tools
        CMAKE_FLAGS="-DGGML_VULKAN=1"
        ;;
    3)
        AI_MODE="CPU"
        echo -e "\n✦ Instalando dependencias base para CPU..."
        sudo pacman -S --needed --noconfirm jq curl git base-devel cmake
        CMAKE_FLAGS=""
        ;;
    *)
        echo "Operación cancelada." ; exit 0 ;;
esac

# 3. Gestión y Compilación de llama.cpp
if [ ! -d "$LLAMA_DIR" ]; then
    echo -e "\n✦ Clonando llama.cpp en $LLAMA_DIR..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMA_DIR"
fi

cd "$LLAMA_DIR" || exit 1
echo -e "\n✦ Compilando llama.cpp para ${YELLOW}$AI_MODE${NC}..."
rm -rf build
cmake -B build $CMAKE_FLAGS
cmake --build build --config Release -j$(nproc)

if [ ! -f "build/bin/llama-server" ]; then
    echo -e "${RED}❌ ERROR: Falló la compilación de llama-server.${NC}"
    exit 1
fi
cd "$PROJECT_ROOT" || exit 1

# 4. Configuración de .env y Enlaces
echo -e "\n✦ Configurando entorno y enlaces simbólicos..."
mkdir -p "$BIN_DEST"
for bin_file in "$PROJECT_ROOT"/bin/*; do
    if [ -f "$bin_file" ]; then
        chmod +x "$bin_file"
        ln -sf "$bin_file" "$BIN_DEST/$(basename "$bin_file")"
    fi
done

# Generar o actualizar .env
if [ ! -f ".env" ]; then
    cat <<EOF > .env
MODEL_REPO=unsloth/Llama-3.2-3B-Instruct-GGUF
MODEL_FILE=Llama-3.2-3B-Instruct-Q4_K_M.gguf
PORT=8081
LLAMA_PATH=$LLAMA_DIR/build/bin/llama-server
AI_API_URL=http://127.0.0.1:8081/v1/chat/completions
AI_BACKUP_DIR=.ai_backups
EOF
fi

# Guardar AI_HARDWARE_MODE
sed -i "/AI_HARDWARE_MODE=/d" .env
echo "AI_HARDWARE_MODE=$AI_MODE" >> .env

# Actualización de PATH en shell
update_shell() {
    local shell_file="$1"
    if [ -f "$shell_file" ]; then
        if ! grep -q "$BIN_DEST" "$shell_file"; then
            echo -e "\n# AI-CLI\nexport PATH=\"\$PATH:$BIN_DEST\"" >> "$shell_file"
            echo "export AI_CLI_ROOT=\"$PROJECT_ROOT\"" >> "$shell_file"
        fi
    fi
}
update_shell "$ZSHRC"
update_shell "$BASHRC"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "✅ ¡CONFIGURACIÓN COMPLETADA CON ÉXITO!"
echo -e "Hardware activo: ${YELLOW}$AI_MODE${NC}"
echo -e "Instrucciones: Ejecuta 'source ~/.zshrc' y luego 'ai-serve'."
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
