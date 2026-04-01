#!/bin/bash
set -e

# ==============================================================================
# AI-CLI CORE v10.0 - Extreme Engineering & Context Agent
# ==============================================================================

# Cargar configuración del .env
SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
[[ -f "$SOURCE_DIR/../.env" ]] && source "$SOURCE_DIR/../.env"

# Configuración base
PORT="${PORT:-8081}"
API_URL="${AI_API_URL:-http://127.0.0.1:$PORT/v1/chat/completions}"
BACKUP_DIR="${AI_BACKUP_DIR:-.ai_backups}"

# Colores y UI Estilo Gemini
RED='\033[0;31m' ; GREEN='\033[0;32m' ; YELLOW='\033[1;33m' ; BLUE='\033[0;34m' ; NC='\033[0m'

draw_read_box() {
    local file="$1"
    echo -e "${BLUE}╭───────────────────────────────────────────╮${NC}"
    printf "${BLUE}│${NC} %-41s ${BLUE}│${NC}\n" "✓ Reading Context: $file"
    echo -e "${BLUE}╰───────────────────────────────────────────╯${NC}"
}

log_info() { echo -e "✦ $1"; }
log_success() { echo -e "${GREEN}✦ $1${NC}"; }
log_warn() { echo -e "${YELLOW}✦ $1${NC}"; }
log_error() { echo -e "${RED}✦ ERROR: $1${NC}" >&2; }

check_dependencies() {
    for cmd in curl jq git diff; do
        command -v $cmd &> /dev/null || { log_error "Falta dependencia: $cmd"; exit 1; }
    done
}

# =========================
# 1. Verificación de Salud
# =========================
check_server_health() {
    local status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://127.0.0.1:$PORT/health")
    if [[ "$status" != "200" ]]; then
        log_error "El servidor no responde (Status: $status). Ejecuta 'ai-serve' primero."
        exit 1
    fi
}

# =========================
# 2. Gestión de Contexto
# =========================
get_auto_context() {
    local context=""
    local files=("package.json" "app/globals.css" "globals.css" "schema.prisma" "prisma/schema.prisma")
    for f in "${files[@]}"; do
        if [[ -f "$f" ]]; then
            draw_read_box "$f"
            context="${context}\n--- FILE: $f ---\n$(cat "$f")\n"
        fi
    done
    echo -e "$context"
}

clean_markdown() {
    # Eliminar bloques de código Markdown y etiquetas de lenguaje de forma segura
    echo "$1" | sed -E 's/^```[a-zA-Z0-9]*//g' | sed -E 's/```$//g' | sed -E 's/^`{3,}$//g' | sed '/^$/d'
}

detect_paths() {
    echo "$1" | grep -oE '([a-zA-Z0-9_\.\/-]+\/[a-zA-Z0-9_\.\/-]+\.[a-z0-9]+|[a-zA-Z0-9_\.-]+\.[a-z0-9]+)' | sort -u
}

get_project_map() {
    find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*'
}

# =========================
# 3. Motor del LLM
# =========================
call_llm_robust() {
    local sys="$1"
    local usr="$2"
    
    check_server_health
    log_info "Pensando en la solución óptima...."

    # Construcción segura de JSON con jq para escapar caracteres especiales
    local payload=$(jq -n \
        --arg sys "$sys" \
        --arg usr "$usr" \
        '{messages: [{role: "system", content: $sys}, {role: "user", content: $usr}], temperature: 0.1, max_tokens: 8000}')

    # Ejecución con captura de código de estado HTTP
    local tmp_res=$(mktemp)
    local http_code=$(curl -s -w "%{http_code}" -o "$tmp_res" -X POST "$API_URL" -H "Content-Type: application/json" -d "$payload")
    
    if [[ "$http_code" != "200" ]]; then
        log_error "Error del servidor LLM (HTTP $http_code). Abortando para proteger el archivo."
        rm -f "$tmp_res"
        exit 1
    fi

    local response=$(cat "$tmp_res")
    rm -f "$tmp_res"

    # Extracción y Validación Anti-Null
    local content=$(echo "$response" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
    
    if [[ -z "$content" || "$content" == "null" ]]; then
        log_error "La IA devolvió una respuesta vacía o 'null'. No se realizarán cambios."
        exit 1
    fi

    echo "$content"
}

# =========================
# 4. Aplicación de Cambios
# =========================
apply_changes() {
    local path="$1"
    local raw_content="$2"
    
    # Limpieza previa del contenido
    local content=$(clean_markdown "$raw_content" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    if [[ ${#content} -lt 10 ]]; then
        log_error "Contenido insuficiente para $path. Abortando escritura."
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
                if cp "$path" "$BACKUP_DIR/$(basename "$path").$(date +%s).bak" && mv "$tmp" "$path"; then
                    log_success "¡Logrado! Archivo $path actualizado correctamente."
                else
                    log_error "Fallo crítico al escribir en $path."
                    exit 1
                fi
            else
                log_warn "Cambios descartados."
                rm -f "$tmp"
            fi
        else
            log_info "No se detectaron cambios reales para $path."
            rm -f "$tmp"
        fi
    else
        echo -e "✦ Nuevo archivo detectado: ${BLUE}$path${NC}"
        read -p "✦ ¿Deseas crear el archivo? (y/n): " confirm
        if [[ "$confirm" == "y" ]]; then
            mkdir -p "$(dirname "$path")"
            if mv "$tmp" "$path"; then
                log_success "¡Logrado! Archivo $path creado con éxito."
            else
                log_error "Error al crear el archivo $path."
                exit 1
            fi
        else
            log_warn "Creación cancelada."
            rm -f "$tmp"
        fi
    fi
}
