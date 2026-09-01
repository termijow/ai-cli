#!/bin/bash
# ==============================================================================
# AI-CLI Services Startup Script — Docker Edition
# Backend (FastAPI :3094) + Frontend (Vite :5173) via Docker Compose
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    case $1 in
        "success") echo -e "${GREEN}✓${NC} $2" ;;
        "warning") echo -e "${YELLOW}⚠${NC} $2" ;;
        "info")    echo -e "${BLUE}ℹ${NC} $2" ;;
        "error")   echo -e "${RED}✗${NC} $2"; exit 1 ;;
    esac
}

if [[ "$1" == "stop" || "$1" == "down" ]]; then
    print_status "info" "Bajando contenedores ai-cli..."
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" down
    print_status "success" "Servicios detenidos."
    exit 0
fi

if [[ "$1" == "status" || "$1" == "check" ]]; then
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps
    exit 0
fi

if [[ "$1" == "restart" ]]; then
    docker compose -f "$SCRIPT_DIR/docker-compose.yml" down
    sleep 1
fi

echo -e "\n${BLUE}╭──────────────────────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│${NC} ${YELLOW}🚀 INICIANDO SERVICIOS AI-CLI (Docker)${NC}          ${BLUE}│${NC}"
echo -e "${BLUE}╰──────────────────────────────────────────────────────────╯${NC}\n"

print_status "info" "Construyendo e iniciando contenedores..."
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d --build 2>&1

# Esperar healthcheck backend
print_status "info" "Esperando backend..."
for i in {1..20}; do
    if curl -sf http://localhost:3094/health > /dev/null 2>&1; then
        print_status "success" "Backend activo: http://localhost:3094"
        break
    fi
    sleep 2
done

# Esperar frontend
print_status "info" "Esperando frontend..."
for i in {1..20}; do
    if curl -sf http://localhost:5173/ > /dev/null 2>&1; then
        print_status "success" "Frontend activo: http://localhost:5173"
        break
    fi
    sleep 2
done

echo -e "\n${GREEN}╭──────────────────────────────────────────────────────────╮${NC}"
echo -e "${GREEN}│${NC} ${GREEN}✨ TODOS LOS SERVICIOS ESTÁN EN EJECUCIÓN${NC}               ${GREEN}│${NC}"
echo -e "${GREEN}├──────────────────────────────────────────────────────────┤${NC}"
echo -e "${GREEN}│${NC} 🌐 Frontend Web Studio: ${YELLOW}http://localhost:5173${NC}"
echo -e "${GREEN}│${NC} ⚙️  Backend REST API:    ${YELLOW}http://localhost:3094${NC}"
echo -e "${GREEN}│${NC} 🧠 LLM llama-server:   ${YELLOW}http://localhost:1234${NC}"
echo -e "${GREEN}╰──────────────────────────────────────────────────────────╯${NC}\n"
echo -e "${BLUE}ℹ  Usa 'ai services stop' para detener.${NC}\n"
