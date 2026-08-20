#!/bin/bash
# show_recent.sh - Función para mostrar registros recientes

echo -e "\n\033[0;32m╭───────────────────────────────────────────────────╮\033[0m"
echo -e "\033[0;32m│\033[0m \033[1;36m📜 REGISTROS RECIENTES\033[0m                        \033[0m"
echo -e "\033[0;32m├───────────────────────────────────────────────────┤\033[0m"

count=0
max_show=10
db="$HOME/.ai_cli_db.db"

# Obtener datos de la BD usando parámetros para evitar conflictos de variables
sqlite3 -separator " | " "$db" "
SELECT 
    strftime('%Y-%m-%d %H:%M', created_at) || ' - ' ||
    COALESCE(input_tokens, 0) || 'k tokens in | ' ||
    COALESCE(output_tokens, 0) || 'k tokens out | ' ||
    COALESCE(input_cost, 0) || ' USD input | ' ||
    COALESCE(output_savings, 0) || ' USD savings | ' ||
    COALESCE(total_savings, 0) || ' USD TOTAL'
FROM usage_logs
ORDER BY rowid DESC
LIMIT $max_show;" | while IFS=' | ' read -r date tokens_in tokens_out cost_in savings total; do
    printf "\033[0;32m│\033[0m \033[1;33m%2d. \033[0m$date %s\033[0m\n" "$((count+1))" "$date" "$((count++))"
done

echo -e "\033[0;32m╰───────────────────────────────────────────────────╯\033[0m"
