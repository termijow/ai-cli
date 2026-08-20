#!/bin/bash

# Registrar uso de AI-CLI
USAGE_SCRIPT="$0"
SCRIPT_DIR="$(dirname "$USAGE_SCRIPT")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "$PROJECT_ROOT/.env"

# Función para registrar uso
register_usage() {
    local input_tokens="$1"
    local output_tokens="$2"
    
    if [[ -z "$input_tokens" ]]; then
        input_tokens=0
    fi
    
    if [[ -z "$output_tokens" ]]; then
        output_tokens=0
    fi
    
    # Calcular costos (precio por 1M tokens = $5 input, $25 output)
    local input_cost=$(echo "scale=2; $input_tokens / 1000000 * 5" | bc)
    local output_savings=$(echo "scale=2; $output_tokens / 1000000 * 25" | bc)
    local total_savings=$(echo "scale=2; $input_cost - $output_savings" | bc)
    
    # Insertar en BD
    sqlite3 "$HOME/.ai_cli_db.db" <<EOF
INSERT INTO usage_logs (input_tokens, output_tokens, input_cost, output_savings, total_savings)
VALUES ($input_tokens, $output_tokens, $input_cost, $output_savings, $total_savings);
EOF
    
    echo "✅ Registro guardado:"
    echo "   Input: $input_tokens tokens | Output: $output_tokens tokens"
    echo "   Input Cost: \$$(printf '%.2f' $input_cost) | Output Savings: \$$(printf '%.2f' $output_savings)"
    echo "   Total Ahorrado: \$$(printf '%.2f' $total_savings)"
}

# Función para mostrar estadísticas
show_stats() {
    echo -e "\n\033[0;32m╭───────────────────────────────────────────────────╮\033[0m"
    echo -e "\033[0;32m│\033[0m \033[1;36m📊 MÉTRICAS HISTÓRICAS TOTALS\033[0m                \033[0;32m│\033[0m"
    echo -e "\033[0;32m├───────────────────────────────────────────────────┤\033[0m"
    
    local total_input_tokens=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(input_tokens), 0) FROM usage_logs;")
    local total_output_tokens=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(output_tokens), 0) FROM usage_logs;")
    local total_input_cost=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(input_cost), 0) FROM usage_logs;")
    local total_output_savings=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(output_savings), 0) FROM usage_logs;")
    local total_savings=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(total_savings), 0) FROM usage_logs;")
    
    echo -e "\033[0;32m│\033[0m \033[1;33mTokens Input Totales:\033[0m \033[1;33m$%-8s\033[0m       \033[0;32m│\033[0m" "$total_input_tokens"
    echo -e "\033[0;32m│\033[0m \033[1;33mTokens Output Totales:\033[0m \033[1;33m$%-8s\033[0m       \033[0;32m│\033[0m" "$total_output_tokens"
    echo -e "\033[0;32m│\033[0m \033[1;33mGasto Input Total:\033[0m \033[1;33m$%-6s USD\033[0m      \033[0;32m│\033[0m" "$(printf '%.2f' $total_input_cost)"
    echo -e "\033[0;32m│\033[0m \033[1;33mAhorro Output Total:\033[0m \033[1;33m$%-6s USD\033[0m      \033[0;32m│\033[0m" "$(printf '%.2f' $total_output_savings)"
    echo -e "\033[0;32m│\033[0m \033[1;32m💰 TOTAL AHORRADO:\033[0m \033[1;32m$%-6s USD\033[0m       \033[0;32m│\033[0m" "$(printf '%.2f' $total_savings)"
    echo -e "\033[0;32m╰───────────────────────────────────────────────────╯\033[0m"
    
    echo -e "\n\033[0;32m╭───────────────────────────────────────────────────╮\033[0m"
    echo -e "\033[0;32m│\033[0m \033[1;36m📈 MÉTRICAS POR MES\033[0m                           \033[0;32m│\033[0m"
    echo -e "\033[0;32m├───────────────────────────────────────────────────┤\033[0m"
    
    # Últimos 6 meses
    local current_month=$(date +%Y-%m)
    for month in $(seq -r 6 1); do
        local month_name=$(date -d "$current_month-$month" +%B 2>/dev/null || date -j -f "%Y-%m-$month" "+%B" 2>/dev/null || echo "$current_month-$month")
        local input_tokens=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(input_tokens), 0) FROM usage_logs WHERE strftime('%Y-%m', created_at) = '$current_month-$month';")
        local output_tokens=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(output_tokens), 0) FROM usage_logs WHERE strftime('%Y-%m', created_at) = '$current_month-$month';")
        local input_cost=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(input_cost), 0) FROM usage_logs WHERE strftime('%Y-%m', created_at) = '$current_month-$month';")
        local output_savings=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(output_savings), 0) FROM usage_logs WHERE strftime('%Y-%m', created_at) = '$current_month-$month';")
        local total_savings=$(sqlite3 "$HOME/.ai_cli_db.db" "SELECT COALESCE(SUM(total_savings), 0) FROM usage_logs WHERE strftime('%Y-%m', created_at) = '$current_month-$month';")
        
        echo -e "\033[0;32m│\033[0m \033[1;33m$month. $month_name:\033[0m \033[1;33m$%-8s tokens\033[0m       \033[0;32m│\033[0m" "$((input_tokens + output_tokens))"
    done
    
    echo -e "\033[0;32m╰───────────────────────────────────────────────────╯\033[0m"
}

# Función para mostrar registros recientes
show_recent() {
    echo -e "\n\033[0;32m╭───────────────────────────────────────────────────╮\033[0m"
    echo -e "\033[0;32m│\033[0m \033[1;36m📜 REGISTROS RECIENTES\033[0m                        \033[0;32m│\033[0m"
    echo -e "\033[0;32m├───────────────────────────────────────────────────┤\033[0m"
    
    count=0
    max_show=10
    sqlite3 -separator " | " "$HOME/.ai_cli_db.db" "SELECT 
        strftime('%Y-%m-%d %H:%M', created_at) || ' - ' || 
        COALESCE(input_tokens, 0) || 'k tokens in | ' || 
        COALESCE(output_tokens, 0) || 'k tokens out | 
        \$$(printf '%.2f' $(SELECT COALESCE(input_cost, 0) FROM usage_logs WHERE rowid=$rowid)) USD input | 
        \$$(printf '%.2f' $(SELECT COALESCE(output_savings, 0) FROM usage_logs WHERE rowid=$rowid)) USD savings | 
        \$$(printf '%.2f' $(SELECT total_savings FROM usage_logs WHERE rowid=$rowid)) USD TOTAL
    FROM usage_logs 
    ORDER BY rowid DESC 
    LIMIT $max_show;" | while read line; do
        printf "\033[0;32m│\033[0m \033[1;33m%d. \033[0m$line\033[0m\n" "$((count+1))"
        ((count++))
    done
    echo -e "\033[0;32m╰───────────────────────────────────────────────────╯\033[0m"
}

case "$1" in
    log)
        # Obtener tokens de argumentos o valores predeterminados
        input_tokens="${2:-0}"
        output_tokens="${3:-0}"
        register_usage "$input_tokens" "$output_tokens"
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
        echo "  ai stats                                - Ver métricas históricas"
        echo "  ai recent                               - Ver registros recientes"
        ;;
esac
