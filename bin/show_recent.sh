#!/bin/bash
# show_recent.sh - Mostrar registros recientes de uso de AI-CLI

echo -e "\n\033[0;32m╭─────────────────────────────────────────────────────────────────────────╮\033[0m"
echo -e "\033[0;32m│\033[0m \033[1;36m📜 REGISTROS RECIENTES (Base de Datos)\033[0m                                   \033[0;32m│\033[0m"
echo -e "\033[0;32m├─────────────────────────────────────────────────────────────────────────┤\033[0m"

db="$HOME/.ai_cli_db.db"
max_show=10
count=1

if [[ -f "$db" ]]; then
    sqlite3 -separator "|" "$db" "
    SELECT 
        strftime('%Y-%m-%d %H:%M', created_at),
        COALESCE(input_tokens, 0),
        COALESCE(output_tokens, 0),
        COALESCE(total_savings, 0)
    FROM usage_logs
    ORDER BY rowid DESC
    LIMIT $max_show;" | while IFS='|' read -r dt in_t out_t total_s; do
        [[ -z "$dt" ]] && continue
        printf "\033[0;32m│\033[0m \033[1;33m%2d.\033[0m %-16s | %5s in / %5s out | \033[1;32mAcumulado: \$%-7s USD\033[0m \033[0;32m│\033[0m\n" \
            "$count" "$dt" "$in_t" "$out_t" "$total_s"
        ((count++))
    done
else
    echo -e "\033[0;32m│\033[0m \033[1;31mNo se encontró la base de datos: $db\033[0m                                    \033[0;32m│\033[0m"
fi

echo -e "\033[0;32m╰─────────────────────────────────────────────────────────────────────────╯\033[0m\n"
