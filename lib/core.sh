#!/bin/bash
set -e

# ==============================================================================
# AI-CLI CORE - V15.0 (Engineering Fixes)
# ==============================================================================

# Cargar configuración del .env
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

if [[ -f "$PROJECT_ROOT/.env" ]]; then
    ENV_FILE="$PROJECT_ROOT/.env"
elif [[ -n "$AI_CLI_ROOT" && -f "$AI_CLI_ROOT/.env" ]]; then
    ENV_FILE="$AI_CLI_ROOT/.env"
else
    # Si no se encuentra el .env, no fallamos aquí porque core.sh 
    # suele ser llamado por bin/ai que ya lo cargó, pero notificamos si falta.
    ENV_FILE=""
fi

[[ -n "$ENV_FILE" ]] && source "$ENV_FILE"

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

    # Sistema de registro de ahorro económico
    # Pricing de referencia: Claude Fable 5 (Input: $10/1M tokens [$0.0000100], Output: $50/1M tokens [$0.0000500])
    local prompt_tokens=$(jq -r '.usage.prompt_tokens // 0' "$tmp_res" 2>/dev/null)
    local completion_tokens=$(jq -r '.usage.completion_tokens // 0' "$tmp_res" 2>/dev/null)

    local prompt_cost=$(awk "BEGIN {printf \"%.4f\", $prompt_tokens * 0.0000100}")
    local output_cost=$(awk "BEGIN {printf \"%.4f\", $completion_tokens * 0.0000500}")
    local total_saving=$(awk "BEGIN {printf \"%.4f\", ($prompt_tokens * 0.0000100) + ($completion_tokens * 0.0000500)}")
    
    local savings_file="$HOME/.ai_cli_savings"
    if [[ ! -f "$savings_file" ]]; then
        echo "0.00" > "$savings_file"
    fi
    local current_savings=$(cat "$savings_file" 2>/dev/null || echo "0.00")
    local new_savings
    new_savings=$(awk "BEGIN {printf \"%.2f\", $current_savings + $total_saving}")
    echo "$new_savings" > "$savings_file"

    # --- Actualización a la base de datos SQLite ---
    local db_file="$HOME/.ai_cli_db.db"
    if [[ -n "$db_file" && -f "$db_file" ]]; then
        # Insertar registro de uso en la base de datos
        sqlite3 "$db_file" "INSERT INTO usage_logs (input_tokens, output_tokens, input_cost, output_savings, total_savings) 
            VALUES ($prompt_tokens, $completion_tokens, $prompt_cost, $output_cost, $new_savings);" 2>/dev/null || true
    fi

    echo -e "\033[0;32m💸 Ahorro vs Claude Fable 5 en esta consulta: \$${total_saving} USD | Total acumulado: \$${new_savings} USD\033[0m" >&2

    # --- Historial de consultas ---
    local history_dir="$HOME/.ai_cli_history"
    local history_file="$history_dir/queries.jsonl"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local query_type="${query_type:-code}"
    
    # Crear directorio de historial si no existe
    mkdir -p "$history_dir"

    # Agregar entrada al historial en formato JSONL (1 línea por consulta)
    local json_entry
    json_entry=$(jq -nc \
        --arg ts "$timestamp" \
        --arg qt "$query_type" \
        --argjson pt "$prompt_tokens" \
        --argjson ct "$completion_tokens" \
        --argjson sv "$total_saving" \
        --argjson tsv "$new_savings" \
        '{"timestamp":$ts, "query_type":$qt, "prompt_tokens":$pt, "completion_tokens":$ct, "savings":$sv, "total_savings":$tsv}' 2>/dev/null)
    
    if [[ -z "$json_entry" ]]; then
        json_entry="{\"timestamp\":\"$timestamp\",\"query_type\":\"$query_type\",\"prompt_tokens\":$prompt_tokens,\"completion_tokens\":$completion_tokens,\"savings\":$total_saving,\"total_savings\":$new_savings}"
    fi
    echo "$json_entry" >> "$history_file"

    # Rotación: mantener las últimas 50 consultas
    local MAX_HISTORY=50
    if [[ -f "$history_file" ]]; then
        tail -n "$MAX_HISTORY" "$history_file" > "${history_file}.tmp" 2>/dev/null && mv "${history_file}.tmp" "$history_file"
    fi

    # --- Fin Historial ---

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
    for cmd in curl jq git diff npx; do
        command -v $cmd &> /dev/null || { log_error "Falta dependencia: $cmd"; exit 1; }
    done
}

# 6. Nueva Funcionalidad 'Auto-QA'
ensure_playwright_config() {
    if [[ ! -f "playwright.config.ts" && ! -f "playwright.config.js" ]]; then
        log_info "No se detectó configuración de Playwright. Creando playwright.config.ts por defecto..."
        cat <<EOF > playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './app/test',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
EOF
        log_success "playwright.config.ts creado."
    fi
}

run_test_loop() {
    local file_path="$1"
    local max_attempts=3
    local attempt=1
    local current_code
    local error_log

    ensure_playwright_config

    while [[ $attempt -le $max_attempts ]]; do
        log_info "Ejecutando Test: $file_path (Intento $attempt/$max_attempts)..."
        
        # Ejecutar test y capturar output/error
        set +e
        error_log=$(npx playwright test "$file_path" 2>&1)
        local status=$?
        set -e

        if [[ $status -eq 0 ]]; then
            log_success "¡El test pasó exitosamente!"
            return 0
        fi

        log_warn "El test falló. Consultando a Gemma para una corrección..."
        
        current_code=$(cat "$file_path")
        
        local sys_prompt=$(get_base_sys_prompt)
        local user_prompt="El test falló con este error: [$error_log]. Aquí está mi código: [$current_code]. Analiza el problema, corrige el código y devuelve la solución completa"

        local proposed_fix=$(call_llm_robust "$sys_prompt" "$user_prompt")
        
        # Guardar temporalmente para mostrar diff y confirmar
        local tmp_fix=$(mktemp)
        echo "$proposed_fix" > "$tmp_fix"

        echo -e "✦ Propuesta de corrección para ${BLUE}$file_path${NC}:"
        diff --color=always -u "$file_path" "$tmp_fix" || true

        read -p "✦ ¿Deseas aplicar esta corrección y volver a probar? (y/n): " confirm
        if [[ "$confirm" == "y" ]]; then
            mv "$tmp_fix" "$file_path"
            log_info "Corrección aplicada. Reintentando..."
        else
            log_warn "Corrección rechazada."
            rm -f "$tmp_fix"
            break
        fi

        attempt=$((attempt + 1))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Se alcanzó el máximo de intentos ($max_attempts) sin éxito."
    fi
    
    read -p "✦ ¿Deseas mantener los cambios aplicados durante el QA? (y/n): " final_confirm
    if [[ "$final_confirm" != "y" ]]; then
        log_info "Revirtiendo cambios (Nota: Esto requiere implementación de historial o git checkout)."
        # En un entorno real, usaríamos backups o git. Por simplicidad en este script:
        log_warn "Se recomienda usar git checkout para revertir si es necesario."
    fi
}

check_server_health() {
    local status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://127.0.0.1:$PORT/health")
    if [[ "$status" != "200" ]]; then
        log_error "El servidor no responde (Status: $status). Ejecuta 'ai-serve' primero."
        exit 1
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 2 ]]; then
        echo -e "${RED}❌ Uso: ai \"PROMPT\" archivo1 [archivo2...]${NC}"
        exit 1
    fi

    PROMPT="$1"
    shift
    FILES="$@"

    check_server_health

    CTX=$(get_auto_context)
    SYS=$(get_base_sys_prompt)

    for file in $FILES; do
        log_info "Procesando $file con Qwen..."
        if [[ -f "$file" ]]; then
            FILE_CONTENT=$(cat "$file")
            USER="Contexto Global:\n$CTX\n\nArchivo Actual: $file\nContenido Actual:\n$FILE_CONTENT\n\nInstrucción: $PROMPT\nDevuelve solo el código modificado, sin bloques markdown ni texto extra."
        else
            USER="Contexto Global:\n$CTX\n\nDebes crear un nuevo archivo en: $file\n\nInstrucción: $PROMPT\nDevuelve solo el código del archivo nuevo, sin bloques markdown extra ni explicaciones."
        fi
        
        NEW_CODE=$(call_llm_robust "$SYS" "$USER")
        apply_changes "$file" "$NEW_CODE"
    done
fi

