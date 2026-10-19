#!/usr/bin/env bash
# ==============================================================================
# Script de descarga secuencial en segundo plano para Linux (0% GPU)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"
PROJECT_ROOT="$(cd -P "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd -P)"
MODELS_DIR="${AI_MODELS_DIR:-$PROJECT_ROOT/models}"

tasks=(
    "Gemma 4 E4B UD-Q8_K_XL (8.11 GB)|https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-UD-Q8_K_XL.gguf|$MODELS_DIR/gemma-4-E4B-it-GGUF/gemma-4-E4B-it-UD-Q8_K_XL.gguf"
    "Ling 3.0 Tiny Q8_0 (7.83 GB)|https://huggingface.co/bartowski/Ling-3.0-tiny-GGUF/resolve/main/Ling-3.0-tiny-Q8_0.gguf|$MODELS_DIR/Ling-3.0-tiny-GGUF/Ling-3.0-tiny-Q8_0.gguf"
)

for entry in "${tasks[@]}"; do
    IFS="|" read -r name url dest <<< "$entry"
    dest_dir="$(dirname "$dest")"
    mkdir -p "$dest_dir"

    echo ""
    echo ">>> [DESCARGANDO]: $name..."
    curl -L -C - "$url" -o "$dest"
    echo ">>> [COMPLETADO]: $name guardado en $dest"
    echo ""
done
