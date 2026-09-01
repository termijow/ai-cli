#!/bin/bash

# Registrar y consultar estadísticas de uso de AI-CLI
export LC_NUMERIC=C

USAGE_SCRIPT="$0"
SCRIPT_DIR="$(dirname "$USAGE_SCRIPT")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

[[ -f "$PROJECT_ROOT/.env" ]] && source "$PROJECT_ROOT/.env"

DB_FILE="$HOME/.ai_cli_db.db"

# Precios de referencia: Claude Fable 5 ($10/1M input, $50/1M output)
# Input: $0.0000100 / token
# Output: $0.0000500 / token

register_usage() {
    local input_tokens="${1:-0}"
    local output_tokens="${2:-0}"
    
    local input_cost_usd=$(awk -v t="$input_tokens" 'BEGIN {printf "%.4f", t * 0.0000100}')
    local output_savings_usd=$(awk -v t="$output_tokens" 'BEGIN {printf "%.4f", t * 0.0000500}')
    local total_savings_usd=$(awk -v in_c="$input_cost_usd" -v out_s="$output_savings_usd" 'BEGIN {printf "%.4f", in_c + out_s}')
    
    # Obtener acumulado previo
    local current_total=$(sqlite3 "$DB_FILE" "SELECT COALESCE(MAX(total_savings), 0) FROM usage_logs;" 2>/dev/null || echo 0)
    local new_accumulated=$(awk -v cur="$current_total" -v cur_save="$total_savings_usd" 'BEGIN {printf "%.2f", cur + cur_save}')

    # Insertar en BD
    sqlite3 "$DB_FILE" "INSERT INTO usage_logs (input_tokens, output_tokens, input_cost, output_savings, total_savings)
        VALUES ($input_tokens, $output_tokens, $input_cost_usd, $output_savings_usd, $new_accumulated);" 2>/dev/null || true
    
    echo "✅ Registro guardado (precios Claude Fable 5):"
    echo "   Input: $input_tokens tokens (\$$input_cost_usd USD) | Output: $output_tokens tokens (\$$output_savings_usd USD)"
    echo "   Ahorro en esta consulta: \$$total_savings_usd USD | Acumulado: \$$new_accumulated USD"
}

show_stats() {
    if [[ -f "$PROJECT_ROOT/bin/ai-sync-savings.py" ]]; then
        python3 "$PROJECT_ROOT/bin/ai-sync-savings.py" --quiet 2>/dev/null || true
    fi

    echo -e "\n\033[0;32m╭───────────────────────────────────────────────────────────╮\033[0m"
    echo -e "\033[0;32m│\033[0m \033[1;36m📊 MÉTRICAS HISTÓRICAS TOTALES (Claude Fable 5)\033[0m            \033[0;32m│\033[0m"
    echo -e "\033[0;32m├───────────────────────────────────────────────────────────┤\033[0m"
    
    local total_input_tokens=$(sqlite3 "$DB_FILE" "SELECT COALESCE(SUM(input_tokens), 0) FROM usage_logs;" 2>/dev/null || echo 0)
    local total_output_tokens=$(sqlite3 "$DB_FILE" "SELECT COALESCE(SUM(output_tokens), 0) FROM usage_logs;" 2>/dev/null || echo 0)
    local total_input_cost=$(sqlite3 "$DB_FILE" "SELECT COALESCE(SUM(input_cost), 0) FROM usage_logs;" 2>/dev/null || echo 0)
    local total_output_savings=$(sqlite3 "$DB_FILE" "SELECT COALESCE(SUM(output_savings), 0) FROM usage_logs;" 2>/dev/null || echo 0)
    local savings_file="$HOME/.ai_cli_savings"
    local total_savings="0.00"
    if [[ -f "$savings_file" ]]; then
        total_savings=$(cat "$savings_file" 2>/dev/null || echo "0.00")
    else
        total_savings=$(sqlite3 "$DB_FILE" "SELECT COALESCE(SUM(input_cost + output_savings), 0) FROM usage_logs;" 2>/dev/null || echo "0.00")
    fi
    
    printf "\033[0;32m│\033[0m \033[1;33mTokens Input Totales:\033[0m   \033[1;32m%12s tokens\033[0m                  \033[0;32m│\033[0m\n" "$total_input_tokens"
    printf "\033[0;32m│\033[0m \033[1;33mTokens Output Totales:\033[0m  \033[1;32m%12s tokens\033[0m                  \033[0;32m│\033[0m\n" "$total_output_tokens"
    printf "\033[0;32m│\033[0m \033[1;33mValor Input Fable 5:\033[0m    \033[1;32m%12.4f USD\033[0m                     \033[0;32m│\033[0m\n" "$total_input_cost"
    printf "\033[0;32m│\033[0m \033[1;33mValor Output Fable 5:\033[0m   \033[1;32m%12.4f USD\033[0m                     \033[0;32m│\033[0m\n" "$total_output_savings"
    printf "\033[0;32m│\033[0m \033[1;32m💰 TOTAL AHORRADO:\033[0m      \033[1;32m%12.2f USD\033[0m                     \033[0;32m│\033[0m\n" "$total_savings"
    echo -e "\033[0;32m╰───────────────────────────────────────────────────────────╯\033[0m"
    
    echo -e "\n\033[0;32m╭───────────────────────────────────────────────────────────╮\033[0m"
    echo -e "\033[0;32m│\033[0m \033[1;36m📈 ACTIVIDAD POR MES (Últimos 6 meses)\033[0m                    \033[0;32m│\033[0m"
    echo -e "\033[0;32m├───────────────────────────────────────────────────────────┤\033[0m"
    
    for i in 0 1 2 3 4 5; do
        local month_key=$(date -d "$i months ago" +%Y-%m 2>/dev/null || date +%Y-%m)
        local month_name=$(date -d "$i months ago" +"%b %Y" 2>/dev/null || echo "$month_key")
        local in_tok=$(sqlite3 "$DB_FILE" "SELECT COALESCE(SUM(input_tokens), 0) FROM usage_logs WHERE strftime('%Y-%m', created_at) = '$month_key';" 2>/dev/null || echo 0)
        local out_tok=$(sqlite3 "$DB_FILE" "SELECT COALESCE(SUM(output_tokens), 0) FROM usage_logs WHERE strftime('%Y-%m', created_at) = '$month_key';" 2>/dev/null || echo 0)
        local tot_tok=$((in_tok + out_tok))
        printf "\033[0;32m│\033[0m  • %-12s:  \033[1;33m%10s tokens\033[0m                            \033[0;32m│\033[0m\n" "$month_name" "$tot_tok"
    done
    
    echo -e "\033[0;32m╰───────────────────────────────────────────────────────────╯\033[0m\n"
}

show_recent() {
    "$PROJECT_ROOT/bin/show_recent.sh"
}

case "$1" in
    log)
        register_usage "${2:-0}" "${3:-0}"
        ;;
    stats)
        show_stats
        ;;
    recent)
        show_recent
        ;;
    *)
        echo "Uso:"
        echo "  ai log <input_tokens> <output_tokens>  - Registrar uso"
        echo "  ai stats                               - Ver métricas históricas"
        echo "  ai recent                              - Ver registros recientes"
        ;;
esac
