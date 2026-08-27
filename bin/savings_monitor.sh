#!/bin/bash
# savings_monitor.sh - Real-time savings display for AI CLI
# Reads and displays current savings from $HOME/.ai_cli_savings

SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

SavingsFile="$HOME/.ai_cli_savings"
DbFile="$HOME/.ai_cli_db.db"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}╭─────────────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│  💰 AHORRO EN TIEMPO REAL - AI CLI ${NC}"
echo -e "${BLUE}╰─────────────────────────────────────────────────╯${NC}\n"

if [[ -f "$SavingsFile" ]]; then
    CURRENT_SAVINGS=$(cat "$SavingsFile")
    echo -e "${GREEN}💸 Total acumulado: \$${CURRENT_SAVINGS} USD${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró archivo de ahorros: $SavingsFile${NC}"
    echo -e "${GREEN}💸 Total acumulado: \$0.00 USD${NC}"
fi

echo ""

if [[ -f "$DbFile" ]]; then
    echo -e "${BLUE}📊 Última consulta registrada:${NC}"
    sqlite3 -separator "|" "$DbFile" "
    SELECT 
        strftime('%Y-%m-%d %H:%M:%S', created_at),
        COALESCE(input_tokens, 0),
        COALESCE(output_tokens, 0),
        ROUND(COALESCE(input_cost, 0) + COALESCE(output_savings, 0), 4),
        COALESCE(total_savings, 0)
    FROM usage_logs
    ORDER BY rowid DESC
    LIMIT 1;" | while IFS='|' read -r dt in_t out_t ses_save tot_s; do
        [[ -n "$dt" ]] && echo -e "${GREEN}  $dt — $in_t in / $out_t out | Ahorro sesión: \$${ses_save} USD | Total: \$${tot_s} USD${NC}"
    done
else
    echo -e "${YELLOW}⚠️  No se encontró base de datos: $DbFile${NC}"
fi
