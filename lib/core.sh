#!/bin/bash

# ==============================================================================
# AI-CLI CORE v6.0 - Professional Context Agent (Gemini Edition)
# ==============================================================================

[[ -f "$(dirname "$(dirname "${BASH_SOURCE[0]}")")/.env" ]] && source "$(dirname "$(dirname "${BASH_SOURCE[0]}")")/.env"

API_URL="${AI_API_URL:-http://localhost:8081/v1/chat/completions}"
BACKUP_DIR="${AI_BACKUP_DIR:-.ai_backups}"
VERBOSE="${AI_VERBOSE:-false}"

RED='\033[0;31m' ; GREEN='\033[0;32m' ; YELLOW='\033[1;33m' ; BLUE='\033[0;34m' ; NC='\033[0m'

# UI Helpers
draw_read_box() {
    local file="$1"
    local label="✓ ReadFile $file"
    echo -e "${BLUE}╭───────────────────────────────────────────╮${NC}"
    printf "${BLUE}│${NC} %-41s ${BLUE}│${NC}\n" "$label"
    echo -e "${BLUE}╰───────────────────────────────────────────╯${NC}"
}

log_info() { echo -e "✦ $1"; }
log_success() { echo -e "${GREEN}✦ $1${NC}"; }
log_warn() { echo -e "${YELLOW}✦ $1${NC}"; }
log_error() { echo -e "${RED}✦ $1${NC}" >&2; }

check_dependencies() {
    for cmd in curl jq git diff; do
        command -v $cmd &> /dev/null || { log_error "Falta dependencia: $cmd"; exit 1; }
    done
}

detect_paths() {
    echo "$1" | grep -oE '([a-zA-Z0-9_\.\/-]+\/[a-zA-Z0-9_\.\/-]+\.[a-z0-9]+|[a-zA-Z0-9_\.-]+\.[a-z0-9]+)' | sort -u
}

get_project_map() {
    find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'
}

get_dynamic_context() {
    local prompt="${1,,}"
    local context=""
    
    # Buscar archivos importantes en el entorno actual
    local important_files=$(find . -maxdepth 2 \( -name "*.css" -o -name "*.prisma" -o -name "*.json" -o -name "tailwind.config.*" \) -not -path '*/.*' -not -path './node_modules*')

    for file in $important_files; do
        local filename=$(basename "$file")
        local ext="${filename##*.}"
        
        # Lógica de relevancia dinámica
        local relevant=false
        [[ "$prompt" == *"estilo"* || "$prompt" == *"color"* || "$prompt" == *"css"* ]] && [[ "$ext" == "css" ]] && relevant=true
        [[ "$prompt" == *"db"* || "$prompt" == *"base de datos"* || "$prompt" == *"prisma"* ]] && [[ "$ext" == "prisma" ]] && relevant=true
        [[ "$prompt" == *"config"* || "$prompt" == *"depen"* || "$prompt" == *"react"* || "$prompt" == *"next"* ]] && [[ "$ext" == "json" ]] && relevant=true
        [[ "$prompt" == *"tailwind"* ]] && [[ "$filename" == *"tailwind.config"* ]] && relevant=true

        if [ "$relevant" = true ]; then
            draw_read_box "$file"
            context="${context}\n--- FILE: $file (Contexto disponible) ---\n$(cat "$file")\n"
        fi
    done
    echo -e "$context"
}

clean_markdown() {
    echo "$1" | sed -e 's/^```[a-zA-Z0-9]*//g' -e 's/^```//g' | sed '/^$/d'
}

validate_content() {
    local content="$1"
    [[ -z "$(echo "$content" | tr -d '[:space:]')" || "$content" == "null" || "$content" == *"error"* ]] && return 1
    return 0
}

call_llm_robust() {
    local sys="$1"
    local usr="$2"
    local attempt=1
    local max_attempts=2

    log_info "Pensando en la solución óptima...."

    while [ $attempt -le $max_attempts ]; do
        local payload
        if [[ "$API_URL" == *"/chat/completions" ]]; then
            payload=$(jq -n --arg sys "$sys" --arg usr "$usr" '{messages: [{role: "system", content: $sys}, {role: "user", content: $usr}], temperature: 0.1, max_tokens: 4000}')
        else
            payload=$(jq -n --arg sys "$sys" --arg usr "$usr" '{prompt: ("<|system|>\n" + $sys + "\n<|user|>\n" + $usr + "\n<|assistant|>\n"), n_predict: 3072, temperature: 0.1, stop: ["<|user|>", "</s>"]}')
        fi

        local response=$(curl -s -f -X POST "$API_URL" -H "Content-Type: application/json" -d "$payload")
        
        if [[ $? -ne 0 ]]; then
            log_error "Servidor LLM no responde. Verifica la conexión en $API_URL"
            exit 1
        fi

        # Capturar y validar el contenido extraído por jq
        local content=$(echo "$response" | jq -r '.content // .choices[0].message.content // empty' 2>/dev/null)

        if [[ -z "$content" || "$content" == "null" ]]; then
            log_error "Error Crítico: La IA devolvió una respuesta vacía o el JSON se rompió. No se realizarán cambios en el archivo."
            exit 1
        fi

        if validate_content "$content"; then
            echo "$content"
            return 0
        fi

        log_warn "Respuesta inválida detectada. Reintentando con exigencia profesional..."
        sys="Eres un Ingeniero de Software Senior. Tu respuesta anterior falló. 
        Misión: Proporcionar código COMPLETO, sin Markdown, sin 'null' y siguiendo mejores prácticas. 
        SOLO CÓDIGO LIMPIO."
        attempt=$((attempt + 1))
    done

    log_error "La IA no pudo generar una respuesta válida. Abortando para proteger el archivo."
    exit 1
}

apply_changes() {
    local path="$1" content="$2"
    
    content=$(clean_markdown "$content" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    if [[ ${#content} -lt 5 ]]; then
        log_error "La IA devolvió contenido vacío o insuficiente. Abortando."
        exit 1
    fi

    local tmp=$(mktemp)
    echo "$content" > "$tmp"

    if [[ -f "$path" ]]; then
        echo -e "✦ Cambios propuestos para ${BLUE}$path${NC}:"
        if ! diff --color=always -u "$path" "$tmp"; then
            read -p "✦ ¿Aplicar cambios? (y/n): " confirm
            if [[ "$confirm" == "y" ]]; then
                mkdir -p "$BACKUP_DIR"
                cp "$path" "$BACKUP_DIR/$(basename "$path").$(date +%s).bak"
                mv "$tmp" "$path"
                log_success "Archivo $path actualizado correctamente."
            else
                log_warn "Cambios descartados."
                rm "$tmp"
            fi
        else
            log_info "No hay cambios detectados para $path."
            rm "$tmp"
        fi
    else
        echo -e "✦ Nuevo archivo detectado: ${BLUE}$path${NC}"
        read -p "✦ ¿Deseas crear el archivo? (y/n): " confirm
        if [[ "$confirm" == "y" ]]; then
            mkdir -p "$(dirname "$path")"
            mv "$tmp" "$path"
            log_success "Archivo $path creado con éxito."
        else
            log_warn "Creación cancelada."
            rm "$tmp"
        fi
    fi
}
