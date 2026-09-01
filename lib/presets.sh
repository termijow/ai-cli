#!/bin/bash
# ==============================================================================
# AI-CLI PRESET MANAGER - Gestión y Carga de Presets por Modelo
# ==============================================================================

# Localizar directorio raíz
_SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}")
_LIB_DIR=$(dirname "$_SCRIPT_PATH")
PROJECT_ROOT=$(dirname "$_LIB_DIR")
PRESETS_DIR="$PROJECT_ROOT/presets"

mkdir -p "$PRESETS_DIR"

# Obtener nombre base del modelo (sin extensión .gguf)
get_model_stem() {
    local m="$1"
    local base=$(basename "$m")
    echo "${base%.gguf}"
}

# Localizar archivo de preset correspondiente a un modelo
find_preset_file() {
    local model_file="$1"
    local stem=$(get_model_stem "$model_file")
    
    # 1. Búsqueda exacta por stem.conf
    if [[ -f "$PRESETS_DIR/$stem.conf" ]]; then
        echo "$PRESETS_DIR/$stem.conf"
        return 0
    fi

    # 2. Búsqueda con .gguf.conf
    if [[ -f "$PRESETS_DIR/$model_file.conf" ]]; then
        echo "$PRESETS_DIR/$model_file.conf"
        return 0
    fi

    # 3. Búsqueda por coincidencia de prefijo (heurística inteligente)
    local match=""
    if [[ "$stem" =~ Qwen3\.5-0\.8B|qwen.*0\.8b|qwen.*0_8b ]]; then
        match=$(find "$PRESETS_DIR" -name "*Qwen3.5-0.8B*.conf" | head -n 1)
    elif [[ "$stem" =~ Qwen3\.5-4B|qwen.*4b ]]; then
        match=$(find "$PRESETS_DIR" -name "*Qwen3.5-4B*.conf" | head -n 1)
    elif [[ "$stem" =~ Qwen3\.5-9B|qwen.*9b ]]; then
        match=$(find "$PRESETS_DIR" -name "*Qwen3.5-9B*.conf" | head -n 1)
    elif [[ "$stem" =~ Qwen3\.6-35B|qwen.*35b ]]; then
        match=$(find "$PRESETS_DIR" -name "*Qwen3.6-35B*.conf" | head -n 1)
    elif [[ "$stem" =~ Qwen3\.8-27B|qwen.*27b ]]; then
        match=$(find "$PRESETS_DIR" -name "*Qwen3.8-27B*.conf" | head -n 1)
    elif [[ "$stem" =~ gemma-4-E4B|gemma.*4b ]]; then
        match=$(find "$PRESETS_DIR" -name "*gemma-4-E4B*.conf" | head -n 1)
    elif [[ "$stem" =~ gemma-4-E2B|gemma.*2b ]]; then
        match=$(find "$PRESETS_DIR" -name "*gemma-4-E2B*.conf" | head -n 1)
    fi

    if [[ -n "$match" && -f "$match" ]]; then
        echo "$match"
        return 0
    fi

    # 4. Fallback default
    if [[ -f "$PRESETS_DIR/default.conf" ]]; then
        echo "$PRESETS_DIR/default.conf"
        return 0
    fi

    echo ""
    return 1
}

# Cargar variables de un preset
load_preset_vars() {
    local preset_file="$1"
    
    # Valores por defecto de seguridad
    PRESET_NAME="Por defecto"
    PRESET_DESC="Configuración estándar"
    PRESET_GPU_LAYERS=35
    PRESET_CTX_SIZE=4096
    PRESET_REASONING="off"
    PRESET_THINKING_LEVEL="off"
    PRESET_BATCH_SIZE=512
    PRESET_UBATCH_SIZE=256
    PRESET_CACHE_TYPE_K="q4_0"
    PRESET_CACHE_TYPE_V="q4_0"
    PRESET_THREADS=""
    PRESET_ESTIMATED_TOKS="~30 tok/s"
    PRESET_MODEL_REPO=""

    if [[ -f "$preset_file" ]]; then
        # Sourced en subshell para no colisionar con el entorno principal si no se desea,
        # pero aquí cargamos directo con parsing seguro
        while IFS='=' read -r key val || [[ -n "$key" ]]; do
            # Ignorar comentarios y líneas vacías
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue
            
            key=$(echo "$key" | tr -d '[:space:]')
            # Quitar comillas del valor
            val=$(echo "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'"'"']//' -e 's/["'"'"']$//')
            
            case "$key" in
                AI_PRESET_NAME)        PRESET_NAME="$val" ;;
                AI_PRESET_DESC)        PRESET_DESC="$val" ;;
                AI_GPU_LAYERS)         PRESET_GPU_LAYERS="$val" ;;
                AI_CTX_SIZE)           PRESET_CTX_SIZE="$val" ;;
                AI_REASONING)          PRESET_REASONING="$val" ;;
                AI_THINKING_LEVEL)     PRESET_THINKING_LEVEL="$val" ;;
                AI_BATCH_SIZE)         PRESET_BATCH_SIZE="$val" ;;
                AI_UBATCH_SIZE)        PRESET_UBATCH_SIZE="$val" ;;
                AI_CACHE_TYPE_K)       PRESET_CACHE_TYPE_K="$val" ;;
                AI_CACHE_TYPE_V)       PRESET_CACHE_TYPE_V="$val" ;;
                AI_THREADS)            PRESET_THREADS="$val" ;;
                AI_MAX_TOKENS)          PRESET_MAX_TOKENS="$val" ;;
                AI_ESTIMATED_TOKS)     PRESET_ESTIMATED_TOKS="$val" ;;
                MODEL_REPO)            PRESET_MODEL_REPO="$val" ;;
            esac
        done < "$preset_file"
    fi
}

# Guardar o actualizar un preset en el repositorio
save_model_preset() {
    local model_file="$1"
    local preset_name="$2"
    local preset_desc="$3"
    local gpu_layers="$4"
    local ctx_size="$5"
    local reasoning="$6"
    local thinking_level="$7"
    local batch_size="$8"
    local ubatch_size="$9"
    local cache_k="${10:-f16}"
    local cache_v="${11:-f16}"
    local estimated_toks="${12:-60+ tok/s}"
    local model_repo="${13:-local/$model_file}"

    local stem=$(get_model_stem "$model_file")
    local target_file="$PRESETS_DIR/$stem.conf"

    cat <<EOF > "$target_file"
# ==============================================================================
# PRESET DE RENDIMIENTO PARA: $model_file
# Generado automáticamente por AI-CLI Presets Manager
# ==============================================================================

AI_PRESET_NAME="$preset_name"
AI_PRESET_DESC="$preset_desc"
AI_ESTIMATED_TOKS="$estimated_toks"

# Configuración del Modelo
MODEL_FILE="$model_file"
MODEL_REPO="$model_repo"

# Configuración GPU / VRAM (RX 6600 8GB)
AI_GPU_LAYERS=$gpu_layers
AI_CTX_SIZE=$ctx_size
AI_BATCH_SIZE=$batch_size
AI_UBATCH_SIZE=$ubatch_size

# Formato de KV Cache (f16 = máxima velocidad / q4_0 = ahorro de VRAM para contextos gigantes)
AI_CACHE_TYPE_K=$cache_k
AI_CACHE_TYPE_V=$cache_v

# Razonamiento / Thinking
AI_REASONING=$reasoning
AI_THINKING_LEVEL=$thinking_level
EOF

    echo "$target_file"
}

# Aplicar preset a .env
apply_preset_to_env_file() {
    local model_file="$1"
    local env_file="$2"
    
    local preset_file=$(find_preset_file "$model_file")
    if [[ -z "$preset_file" || ! -f "$preset_file" ]]; then
        return 1
    fi

    load_preset_vars "$preset_file"

    # Actualizar variables en .env
    sed -i "s|^MODEL_FILE=.*|MODEL_FILE=$model_file|" "$env_file"
    [[ -n "$PRESET_MODEL_REPO" ]] && sed -i "s|^MODEL_REPO=.*|MODEL_REPO=$PRESET_MODEL_REPO|" "$env_file"
    sed -i "s|^AI_GPU_LAYERS=.*|AI_GPU_LAYERS=$PRESET_GPU_LAYERS|" "$env_file"
    
    if grep -q "^AI_CTX_SIZE=" "$env_file"; then
        sed -i "s|^AI_CTX_SIZE=.*|AI_CTX_SIZE=$PRESET_CTX_SIZE|" "$env_file"
    else
        echo "AI_CTX_SIZE=$PRESET_CTX_SIZE" >> "$env_file"
    fi

    if grep -q "^AI_REASONING=" "$env_file"; then
        sed -i "s|^AI_REASONING=.*|AI_REASONING=$PRESET_REASONING|" "$env_file"
    else
        echo "AI_REASONING=$PRESET_REASONING" >> "$env_file"
    fi

    if grep -q "^AI_THINKING_LEVEL=" "$env_file"; then
        sed -i "s|^AI_THINKING_LEVEL=.*|AI_THINKING_LEVEL=$PRESET_THINKING_LEVEL|" "$env_file"
    else
        echo "AI_THINKING_LEVEL=$PRESET_THINKING_LEVEL" >> "$env_file"
    fi

    # Batch / Cache vars
    if grep -q "^AI_BATCH_SIZE=" "$env_file"; then
        sed -i "s|^AI_BATCH_SIZE=.*|AI_BATCH_SIZE=$PRESET_BATCH_SIZE|" "$env_file"
    else
        echo "AI_BATCH_SIZE=$PRESET_BATCH_SIZE" >> "$env_file"
    fi

    if grep -q "^AI_UBATCH_SIZE=" "$env_file"; then
        sed -i "s|^AI_UBATCH_SIZE=.*|AI_UBATCH_SIZE=$PRESET_UBATCH_SIZE|" "$env_file"
    else
        echo "AI_UBATCH_SIZE=$PRESET_UBATCH_SIZE" >> "$env_file"
    fi

    if grep -q "^AI_CACHE_TYPE_K=" "$env_file"; then
        sed -i "s|^AI_CACHE_TYPE_K=.*|AI_CACHE_TYPE_K=$PRESET_CACHE_TYPE_K|" "$env_file"
    else
        echo "AI_CACHE_TYPE_K=$PRESET_CACHE_TYPE_K" >> "$env_file"
    fi

    if grep -q "^AI_CACHE_TYPE_V=" "$env_file"; then
        sed -i "s|^AI_CACHE_TYPE_V=.*|AI_CACHE_TYPE_V=$PRESET_CACHE_TYPE_V|" "$env_file"
    else
        echo "AI_CACHE_TYPE_V=$PRESET_CACHE_TYPE_V" >> "$env_file"
    fi

    return 0
}
