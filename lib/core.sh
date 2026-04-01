#!/bin/bash

# ==============================================================================
# AI-CLI CORE v5.2 - Gemini UI Edition
# ==============================================================================

[[ -f "$(dirname "$(dirname "${BASH_SOURCE[0]}")")/.env" ]] && source "$(dirname "$(dirname "${BASH_SOURCE[0]}")")/.env"

API_URL="${AI_API_URL:-http://localhost:8080/completion}"
BACKUP_DIR="${AI_BACKUP_DIR:-.ai_backups}"
VERBOSE="${AI_VERBOSE:-false}"

RED='\033[0;31m' ; GREEN='\033[0;32m' ; YELLOW='\033[1;33m' ; BLUE='\033[0;34m' ; NC='\033[0m'

# Helpers de UI Estilo Gemini
draw_read_box() {
    local file="$1"
    local label="✓ ReadFile $file"
    local width=45
    echo -e "${BLUE}╭───────────────────────────────────────────╮${NC}"
    printf "${BLUE}│${NC} %-41s ${BLUE}│${NC}\n" "$label"
    echo -e "${BLUE}╰───────────────────────────────────────────╯${NC}"
}

log_info() { echo -e "✦ $1"; }
log_success() { echo -e "${GREEN}✦ $1${NC}"; }
log_warn() { echo -e "${YELLOW}✦ $1${NC}"; }
log_error() { echo -e "${RED}✦ ERROR: $1${NC}" >&2; }
log_debug() { [[ "$VERBOSE" == "true" ]] && echo -e "${BLUE}✦ DEBUG: $1${NC}"; }

check_dependencies() {
    for cmd in curl jq git diff; do
        command -v $cmd &> /dev/null || { log_error "Falta dependencia: $cmd"; exit 1; }
    done
}

get_project_map() {
    find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'
}

get_dynamic_context() {
    local prompt="$1"
    local context=""
    
    # Mapeo extendido con lógica React/Nextjs
    declare -A context_map=(
        ["color"]="app/globals.css globals.css tailwind.config.ts"
        ["estilo"]="app/globals.css globals.css tailwind.config.ts"
        ["react"]="package.json next.config.mjs next.config.js"
        ["next"]="package.json next.config.mjs next.config.js"
        ["base de datos"]="prisma/schema.prisma schema.prisma"
        ["prisma"]="prisma/schema.prisma"
        ["config"]="tailwind.config.ts package.json .env.example"
    )

    for key in "${!context_map[@]}"; do
        if [[ "${prompt,,}" == *"$key"* ]]; then
            for file in ${context_map[$key]}; do
                if [[ -f "$file" ]]; then
                    draw_read_box "$file"
                    context="${context}\n--- FILE: $file ---\n$(cat "$file")\n"
                fi
            done
        fi
    done
    echo -e "$context"
}

clean_markdown() {
    local input="$1"
    echo "$input" | sed -e 's/^```[a-zA-Z0-9]*//g' -e 's/^```//g' | sed '/^$/d'
}

validate_content() {
    local content="$1"
    local forbidden=("pass" "clean_code" "TODO" "insert logic" "placeholders")
    
    [[ -z "$(echo "$content" | tr -d '[:space:]')" || "$content" == "null" ]] && return 1
    for word in "${forbidden[@]}"; do
        if echo "$content" | grep -qi "$word"; then return 1; fi
    done
    return 0
}

call_llm_robust() {
    local sys="$1"
    local usr="$2"
    local attempt=1
    local max_attempts=2

    log_info "Pensando en cómo resolver tu petición..."

    while [ $attempt -le $max_attempts ]; do
        local payload
        if [[ "$API_URL" == *"/chat/completions" ]]; then
            payload=$(jq -n --arg sys "$sys" --arg usr "$usr" '{messages: [{role: "system", content: $sys}, {role: "user", content: $usr}], temperature: 0.1}')
        else
            payload=$(jq -n --arg sys "$sys" --arg usr "$usr" '{prompt: ("<|system|>\n" + $sys + "\n<|user|>\n" + $usr + "\n<|assistant|>\n"), n_predict: 3072, temperature: 0.1}')
        fi

        local response=$(curl -s -f -X POST "$API_URL" -H "Content-Type: application/json" -d "$payload")
        [[ $? -ne 0 ]] && { log_error "Servidor LLM no responde."; return 1; }

        local content=$(echo "$response" | jq -r '.content // .choices[0].message.content // empty' 2>/dev/null)

        if validate_content "$content"; then
            echo "$content"
            return 0
        fi
        attempt=$((attempt + 1))
    done
    return 1
}

apply_changes() {
    local path="$1" content="$2"
    
    if [[ -z "$content" || "$content" == "null" ]]; then
        log_error "Respuesta inválida de la IA para $path."
        return 1
    fi

    content=$(clean_markdown "$content" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    local tmp=$(mktemp)
    echo "$content" > "$tmp"

    if [[ -f "$path" ]]; then
        echo -e "✦ Cambios propuestos para ${BLUE}$path${NC}:"
        if ! diff --color=always -u "$path" "$tmp"; then
            read -p "✦ ¿Aplicar cambios? (y/n): " c
            if [[ "$c" == "y" ]]; then
                mkdir -p "$BACKUP_DIR"
                cp "$path" "$BACKUP_DIR/$(basename "$path").$(date +%s).bak"
                mv "$tmp" "$path"
                log_success "Archivo actualizado."
            else
                log_warn "Cambios descartados."
                rm "$tmp"
            fi
        else
            log_info "No hay cambios pendientes."
            rm "$tmp"
        fi
    else
        echo -e "✦ Nuevo archivo detectado: ${BLUE}$path${NC}"
        read -p "✦ ¿Deseas crear este archivo? (y/n): " c
        if [[ "$c" == "y" ]]; then
            mkdir -p "$(dirname "$path")"
            mv "$tmp" "$path"
            log_success "Archivo creado."
        else
            rm "$tmp"
        fi
    fi
}


