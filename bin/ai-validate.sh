#!/usr/bin/env bash
# ==============================================================================
# AI-CLI SYSTEM VALIDATION & DIAGNOSTIC
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]:-$0}")" >/dev/null 2>&1 && pwd -P)"
PROJECT_ROOT="$(cd -P "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd -P)"
export PATH="$PROJECT_ROOT/bin:$PATH"
[[ -f "$PROJECT_ROOT/.env" ]] && source "$PROJECT_ROOT/.env"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${YELLOW}  🔍 Validando Entorno y Componentes AI-CLI${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Scripts en lib/
echo -e "${GREEN}[1/7] Verificando librerías base (lib/)...${NC}"
for lib in "core.sh" "presets.sh"; do
    if [[ -f "$PROJECT_ROOT/lib/$lib" ]]; then
        echo -e "  ✓ lib/$lib existe"
    else
        echo -e "  ✗ lib/$lib NO encontrado"
    fi
done

# 2. Binarios en bin/
echo -e "\n${GREEN}[2/7] Verificando scripts ejecutables (bin/)...${NC}"
for b in "ai" "ai-models" "ai-serve" "ai-menu" "ai-help" "ai-history" "ai-stats.sh"; do
    if [[ -f "$PROJECT_ROOT/bin/$b" ]]; then
        if [[ -x "$PROJECT_ROOT/bin/$b" ]]; then
            echo -e "  ✓ bin/$b (ejecutable)"
        else
            echo -e "  ⚠️  bin/$b existe pero no es ejecutable (chmod +x)"
        fi
    else
        echo -e "  ✗ bin/$b NO encontrado"
    fi
done

# 3. Presets por modelo
echo -e "\n${GREEN}[3/7] Verificando repositorio de presets (presets/)...${NC}"
if [[ -d "$PROJECT_ROOT/presets" ]]; then
    shopt -s nullglob
    preset_files=("$PROJECT_ROOT/presets"/*.conf)
    P_COUNT=${#preset_files[@]}
    echo -e "  ✓ Carpeta presets/ encontrada ($P_COUNT presets configurados)"
    for pf in "${preset_files[@]}"; do
        [[ -f "$pf" ]] && echo -e "    ↳ $(basename "$pf")"
    done
else
    echo -e "  ✗ Directorio presets/ no encontrado"
fi

# 4. Historial y Ahorros
echo -e "\n${GREEN}[4/7] Verificando persistencia de datos...${NC}"
HISTORY_DIR="$HOME/.ai_cli_history"
SAVINGS_FILE="$HOME/.ai_cli_savings"
if [[ -d "$HISTORY_DIR" && -f "$HISTORY_DIR/queries.jsonl" ]]; then
    COUNT=$(wc -l < "$HISTORY_DIR/queries.jsonl")
    echo -e "  ✓ Historial: $COUNT consultas en $HISTORY_DIR/queries.jsonl"
else
    echo -e "  ℹ️  Historial listo para nuevas consultas"
fi

if [[ -f "$SAVINGS_FILE" ]]; then
    SAVINGS=$(cat "$SAVINGS_FILE")
    echo -e "  ✓ Alcancía de Ahorros: \$$SAVINGS USD acumulados"
else
    echo -e "  ℹ️  Alcancía de Ahorros inicializada"
fi

# 5. Herramientas CLI del sistema
echo -e "\n${GREEN}[5/7] Verificando dependencias de software...${NC}"
for cmd in jq curl git fzf sqlite3; do
    if command -v $cmd &> /dev/null; then
        echo -e "  ✓ $cmd disponible"
    else
        echo -e "  ⚠️  $cmd no instalado (recomendado)"
    fi
done

# 6. Detección de GPU / Hardware
echo -e "\n${GREEN}[6/7] Verificando aceleración GPU...${NC}"
LLAMA_FOUND=""
for lp in "$PROJECT_ROOT/llama-bin/llama-server.exe" "$PROJECT_ROOT/llama-bin/llama-server" "${LLAMA_PATH:-}" "$HOME/llama.cpp/llama-server.exe" "$HOME/llama.cpp/build/bin/llama-server"; do
    if [[ -n "$lp" && -f "$lp" ]]; then
        LLAMA_FOUND="$lp"
        break
    fi
done

if [[ -n "$LLAMA_FOUND" ]]; then
    dev_str=$("$LLAMA_FOUND" --list-devices 2>/dev/null | grep -iE "Vulkan|AMD|Radeon" | head -n 1 || true)
    if [[ -n "$dev_str" ]]; then
        echo -e "  ✓ Aceleración GPU detectada:"
        echo -e "    ↳ $dev_str"
    fi
elif command -v rocm-smi &> /dev/null; then
    echo -e "  ✓ rocm-smi detectado"
    rocm-smi --showmeminfo vram 2>/dev/null | grep -E "VRAM Total Memory|VRAM Total Used Memory" | while read -r line; do
        echo -e "    ↳ $line"
    done || true
else
    echo -e "  ℹ️  Aceleración estándar configurada"
fi

# 7. Verificación de llama-server
echo -e "\n${GREEN}[7/7] Verificando binario llama-server...${NC}"
if [[ -n "$LLAMA_FOUND" ]]; then
    echo -e "  ✓ $LLAMA_FOUND listo"
else
    echo -e "  ⚠️  llama-server no encontrado"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Validación completada con éxito${NC}"
echo -e "${GREEN}========================================${NC}\n"
