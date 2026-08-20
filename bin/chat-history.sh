#!/bin/bash
# Chat history integration for llama.cpp and Qwen
# Este script se ejecuta después de cualquier sesión de chat

# Detectar si estamos en el proyecto
if [[ ! -f "$HOME/.qwen/history.json" ]]; then
    exit 0
fi

# Leer la última sesión del chat
LAST_SESSION=$(cat "$HOME/.qwen/history.json" 2>/dev/null | jq -r '.sessions | -1 | . + 1' 2>/dev/null)

if [[ -z "$LAST_SESSION" || "$LAST_SESSION" == "null" ]]; then
    exit 0
fi

# Obtener los tokens de la última sesión
if [[ -f "$HOME/.qwen/history.json" ]]; then
    LAST_PROMPT=$(cat "$HOME/.qwen/history.json" | jq -r ".sessions[$LAST_SESSION].prompt_tokens // 0" 2>/dev/null)
    LAST_COMPLETION=$(cat "$HOME/.qwen/history.json" | jq -r ".sessions[$LAST_SESSION].completion_tokens // 0" 2>/dev/null)
    LAST_TIMESTAMP=$(cat "$HOME/.qwen/history.json" | jq -r ".sessions[$LAST_SESSION].timestamp // \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"" 2>/dev/null)
else
    LAST_PROMPT=0
    LAST_COMPLETION=0
    LAST_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fi

# Si no hay tokens, no guardar
if [[ $LAST_PROMPT -eq 0 && $LAST_COMPLETION -eq 0 ]]; then
    exit 0
fi

# Calcular el ahorro simulado
PROMPT_COST=$(awk "BEGIN {printf \"%.6f\", $LAST_PROMPT * 0.0000050}")
COMPLETION_COST=$(awk "BEGIN {printf \"%.6f\", $LAST_COMPLETION * 0.0000100}")
TOTAL_SAVING=$(awk "BEGIN {printf \"%.4f\", $PROMPT_COST + $COMPLETION_COST}")

# Actualizar el total de ahorros
SAVINGS_FILE="$HOME/.ai_cli_savings"
if [[ ! -f "$SAVINGS_FILE" ]]; then
    echo "0.00" > "$SAVINGS_FILE"
fi
CURRENT_SAVINGS=$(cat "$SAVINGS_FILE")
NEW_SAVINGS=$(awk "BEGIN {printf \"%.2f\", $CURRENT_SAVINGS + $TOTAL_SAVING}")
echo "$NEW_SAVINGS" > "$SAVINGS_FILE"

# Crear entrada para el historial
HISTORY_DIR="$HOME/.ai_cli_history"
HISTORY_FILE="$HISTORY_DIR/queries.jsonl"
mkdir -p "$HISTORY_DIR"

NEW_ENTRY="{\"timestamp\":\"$LAST_TIMESTAMP\",\"query_type\":\"chat\",\"prompt_tokens\":$LAST_PROMPT,\"completion_tokens\":$LAST_COMPLETION,\"savings\":$TOTAL_SAVING,\"total_savings\":$NEW_SAVINGS}"

# Agregar nueva entrada
echo "$NEW_ENTRY" >> "$HISTORY_FILE"

# Rotación: mantener solo las últimas 20 entradas
MAX_HISTORY=20
ENTRY_COUNT=$(wc -l < "$HISTORY_FILE" 2>/dev/null || echo 0)
if [[ $ENTRY_COUNT -gt $MAX_HISTORY ]]; then
    KEEP_COUNT=$((ENTRY_COUNT - MAX_HISTORY))
    head -n "$KEEP_COUNT" "$HISTORY_FILE" > "${HISTORY_FILE}.tmp" && mv "${HISTORY_FILE}.tmp" "$HISTORY_FILE"
fi

exit 0
