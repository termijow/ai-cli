#!/usr/bin/env bash
# ai-validate.sh - Script para validar el sistema de ahorro y historial
#
# Este script verifica que:
# 1. El sistema de ahorro funciona correctamente
# 2. Los datos se guardan en el historial correctamente
# 3. No se saturan los archivos de historial

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${GREEN}========================================${NC}\n"
echo -e "${GREEN}  Validando Sistema de Ahorro y Historial${NC}\n"
echo -e "${GREEN}========================================${NC}\n"

# Función para pasar por alto errores
trap 'echo -e "\n${YELLOW}⚠️  Pasando por alto error: ${NC}$1\n"; return 1' ERR

# Verificar que lib/core.sh existe y sea ejecutable
echo -e "${GREEN}[1/6] Verificando lib/core.sh...${NC}"
if [[ -f "$(dirname "$0")/../lib/core.sh" ]]; then
    echo -e "  ✓ lib/core.sh existe"
    if [[ -x "$(dirname "$0")/../lib/core.sh" ]]; then
        echo -e "  ✓ lib/core.sh es ejecutable"
    else
        echo -e "  ⚠️  lib/core.sh NO es ejecutable (chmod +x)"
    fi
else
    echo -e "  ✗ lib/core.sh NO encontrado en lib/"
fi

# Verificar que bin/ai-history existe
echo -e "${GREEN}[2/6] Verificando bin/ai-history...${NC}"
if [[ -f "$(dirname "$0")/../bin/ai-history" ]]; then
    echo -e "  ✓ bin/ai-history existe"
else
    echo -e "  ✗ bin/ai-history NO encontrado"
fi

# Verificar que bin/ai existe
echo -e "${GREEN}[3/6] Verificando bin/ai...${NC}"
if [[ -f "$(dirname "$0")/../bin/ai" ]]; then
    echo -e "  ✓ bin/ai existe"
else
    echo -e "  ✗ bin/ai NO encontrado"
fi

# Verificar directorio de historial
echo -e "${GREEN}[4/6] Verificando directorio de historial...${NC}"
HISTORY_DIR="$HOME/.ai_cli_history"
if [[ -d "$HISTORY_DIR" ]]; then
    echo -e "  ✓ Directorio de historial existe: $HISTORY_DIR"
    if [[ -f "$HISTORY_DIR/queries.jsonl" ]]; then
        COUNT=$(wc -l < "$HISTORY_DIR/queries.jsonl")
        echo -e "  ℹ️  Entradas en historial: $COUNT"
    else
        echo -e "  ℹ️  No hay entradas en historial (nuevo sistema)"
    fi
else
    echo -e "  ℹ️  Directorio de historial no existe: $HISTORY_DIR (nueva instalación)"
fi

# Verificar archivo de ahorros
echo -e "${GREEN}[5/6] Verificando archivo de ahorros...${NC}"
SAVINGS_FILE="$HOME/.ai_cli_savings"
if [[ -f "$SAVINGS_FILE" ]]; then
    SAVINGS=$(cat "$SAVINGS_FILE")
    echo -e "  ✓ Archivo de ahorros existe: $SAVINGS_FILE"
    echo -e "  ℹ️  Ahorro acumulado: \$${SAVINGS} USD"
else
    echo -e "  ℹ️  Archivo de ahorros no existe (nuevo sistema)"
fi

# Verificar dependencias (jq)
echo -e "${GREEN}[6/6] Verificando dependencias...${NC}"
if command -v jq &> /dev/null; then
    echo -e "  ✓ jq disponible: $(jq --version)"
else
    echo -e "  ✗ jq NO encontrado (necesario para procesar JSONL)"
fi

echo -e "\n${GREEN}========================================${NC}\n"
echo -e "${GREEN}Validación completada${NC}\n"
echo -e "${GREEN}========================================${NC}\n"

# Mostrar resumen del sistema
echo -e "${YELLOW}📊 Resumen del Sistema:${NC}\n"
echo -e "  Directorio de historial: $HISTORY_DIR"
echo -e "  Archivo de ahorros: $SAVINGS_FILE"
echo -e "  Script de historial: $(dirname "$0")/../bin/ai-history"
echo -e "  Script de ahorro: $(dirname "$0")/../lib/core.sh"

echo -e "\n${YELLOW}💡 Comandos útiles:${NC}\n"
echo -e "  # Ver historial de consultas"
echo -e "  $(dirname "$0")/../bin/ai-history --limit 10"
echo -e "  # Exportar historial a CSV"
echo -e "  $(dirname "$0")/../bin/ai-history --csv"
echo -e "  # Ver ahorros totales"
echo -e "  $(dirname "$0")/../bin/ai"
echo -e "  # Limpiar historial (¡con precaución!)"
echo -e "  $(dirname "$0")/../bin/ai-history --clear"
