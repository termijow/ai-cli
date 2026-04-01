#!/bin/bash
set -e

# ==============================================================================
# AI-CLI CORE - V15.0 (Engineering Fixes)
# ==============================================================================

# Cargar configuración del .env
SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
[[ -f "$SOURCE_DIR/../.env" ]] && source "$SOURCE_DIR/../.env"

# Colores y UI Estilo Gemini
RED='\033[0;31m' ; GREEN='\033[0;32m' ; YELLOW='\033[1;33m' ; BLUE='\033[0;34m' ; NC='\033[0m'

# Configuración base
PORT="${PORT:-8081}"
API_URL="${AI_API_URL:-http://127.0.0.1:$PORT/v1/chat/completions}"
BACKUP_DIR="${AI_BACKUP_DIR:-.ai_backups}"

# 1. UI Gemini
draw_read_box() {
    local file="$1"
    echo -e "${BLUE}╭───────────────────────────────────────────╮${NC}"
    printf "${BLUE}│${NC} %-41s ${BLUE}│${NC}\n" "✓ Read Context: $file"
    echo -e "${BLUE}╰───────────────────────────────────────────╯${NC}"
}

log_info() { echo -e "✦ $1"; }
log_success() { echo -e "${GREEN}✦ $1${NC}"; }
log_warn() { echo -e "${YELLOW}✦ $1${NC}"; }
log_error() { echo -e "${RED}✦ ERROR: $1${NC}" >&2; }

# 2. Gestión de Contexto Automático
get_auto_context() {
    local context=""
    local key_files=("package.json" "globals.css" "app/globals.css" "schema.prisma" "prisma/schema.prisma" "tailwind.config.ts" "tailwind.config.js")
    for f in "${key_files[@]}"; do
        if [[ -f "$f" ]]; then
            draw_read_box "$f"
            context+=$'\n--- FILE: '"$f"' ---\n'
            context+="$(cat "$f")"$'\n'
        fi
    done
    echo "$context"
}

# 3. Filtro de Output
clean_markdown() {
    echo "$1" | sed '/^```/d' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

# 4. Motor del LLM (Robustez Crítica)
call_llm_robust() {
    local sys="$1"
    local usr="$2"
    local temp="0.2"

    log_info "Analizando con IA (Temp: $temp)..."

    local payload
    payload=$(jq -n \
        --arg sys "$sys" \
        --arg user "$usr" \
        --argjson t "$temp" \
        '{"messages": [{"role": "system", "content": $sys}, {"role": "user", "content": $user}], "temperature": $t}')

    local tmp_res=$(mktemp)
    local http_code
    
    http_code=$(curl -s -o "$tmp_res" -w "%{http_code}" \
        -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    if [[ "$http_code" != "200" ]]; then
        log_error "El servidor falló (Status: $http_code)."
        cat "$tmp_res" >&2
        rm -f "$tmp_res"
        exit 1
    fi

    local content
    content=$(jq -r '.choices[0].message.content // empty' "$tmp_res" 2>/dev/null)
    rm -f "$tmp_res"

    # Robustez: Protección Crítica contra 'null'
    if [[ -z "$content" || "$content" == "null" ]]; then
        echo -e "${RED}❌ Error: La respuesta de la IA fue nula.${NC}"
        exit 1
    fi

    clean_markdown "$content"
}

# 5. Utilidades de Archivos (Fix Grep)
detect_paths() {
    # Regex exacto para evitar error de 'stray \'
    echo "$1" | grep -oE '[a-zA-Z0-9._/-]+\.[a-zA-Z0-9]+' | sort -u
}

get_base_sys_prompt() {
    echo "Eres un Ingeniero Senior de Software. Genera código limpio, moderno e idiomático."
}

apply_changes() {
    local path="$1"
    local raw_content="$2"
    local content=$(clean_markdown "$raw_content")
    
    if [[ ${#content} -lt 1 ]]; then
        log_error "Contenido vacío. No se aplicarán cambios a $path."
        exit 1
    fi

    local tmp=$(mktemp)
    echo "$content" > "$tmp"

    if [[ -f "$path" ]]; then
        echo -e "✦ Cambios propuestos para ${BLUE}$path${NC}:"
        if ! diff --color=always -u "$path" "$tmp"; then
            read -p "✦ ¿Deseas aplicar estos cambios? (y/n): " confirm
            if [[ "$confirm" == "y" ]]; then
                mkdir -p "$BACKUP_DIR"
                cp "$path" "$BACKUP_DIR/$(basename "$path").$(date +%s).bak"
                mv "$tmp" "$path"
                log_success "¡Logrado! El archivo $path ha sido actualizado."
            else
                log_warn "Cambios descartados para $path."
                rm -f "$tmp"
            fi
        else
            log_info "No se detectaron diferencias para $path."
            rm -f "$tmp"
        fi
    else
        echo -e "✦ Detectado nuevo archivo: ${BLUE}$path${NC}"
        read -p "✦ ¿Confirmas la creación del archivo? (y/n): " confirm
        if [[ "$confirm" == "y" ]]; then
            mkdir -p "$(dirname "$path")"
            mv "$tmp" "$path"
            log_success "¡Logrado! Archivo $path creado con éxito."
        else
            log_warn "Creación de $path cancelada."
            rm -f "$tmp"
        fi
    fi
}

check_dependencies() {
    for cmd in curl jq git diff; do
        command -v $cmd &> /dev/null || { log_error "Falta dependencia: $cmd"; exit 1; }
    done
}

check_server_health() {
    local status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://127.0.0.1:$PORT/health")
    if [[ "$status" != "200" ]]; then
        log_error "El servidor no responde (Status: $status). Ejecuta 'ai-serve' primero."
        exit 1
    fi
}
