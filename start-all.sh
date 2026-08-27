#!/bin/bash
# ==============================================================================
# AI-CLI Services Startup Script
# Starts Backend (FastAPI :3094) and Frontend (Vite :5173) cleanly
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Virtualenv Python detection
if [[ -f "$SCRIPT_DIR/venv/bin/python" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
else
    echo "❌ ERROR: No se encontró Python 3."
    exit 1
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

BACKEND_PORT=${BACKEND_PORT:-3094}
BACKEND_HOST=${BACKEND_HOST:-0.0.0.0}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

print_status() {
    local status=$1
    local message=$2
    case $status in
        "success") echo -e "${GREEN}✓${NC} $message" ;;
        "warning") echo -e "${YELLOW}⚠${NC} $message" ;;
        "info")    echo -e "${BLUE}ℹ${NC} $message" ;;
        "error")   echo -e "${RED}✗${NC} $message"; exit 1 ;;
    esac
}

# Handle 'stop' or 'down' upfront
if [[ "$1" == "stop" || "$1" == "down" ]]; then
    pkill -f "uvicorn server:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    fuser -k 3094/tcp 2>/dev/null || true
    fuser -k 5173/tcp 2>/dev/null || true
    print_status "success" "Servicios backend y frontend detenidos."
    exit 0
fi

port_in_use() {
    local port=$1
    if command -v ss &> /dev/null; then
        ss -tln 2>/dev/null | grep -q ":$port "
    elif command -v netstat &> /dev/null; then
        netstat -tln 2>/dev/null | grep -q ":$port "
    elif command -v lsof &> /dev/null; then
        lsof -i -P -n 2>/dev/null | grep -q ":$port"
    else
        return 1
    fi
}

echo -e "\n${BLUE}╭──────────────────────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│${NC} ${YELLOW}🚀 INICIANDO SERVICIOS AI-CLI (Backend + Frontend)${NC}      ${BLUE}│${NC}"
echo -e "${BLUE}╰──────────────────────────────────────────────────────────╯${NC}\n"

# 1. Start Backend Server
print_status "info" "Iniciando Backend Server en puerto $BACKEND_PORT..."

if port_in_use "$BACKEND_PORT"; then
    print_status "warning" "Puerto $BACKEND_PORT en uso. Reiniciando proceso..."
    pkill -f "uvicorn server:app" 2>/dev/null || true
    sleep 1
fi

cd "$BACKEND_DIR"
if command -v setsid &>/dev/null; then
    setsid "$PYTHON_BIN" -m uvicorn server:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload --log-level info < /dev/null > "$BACKEND_DIR/server.log" 2>&1 &
else
    nohup "$PYTHON_BIN" -m uvicorn server:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload --log-level info < /dev/null > "$BACKEND_DIR/server.log" 2>&1 &
fi
BACKEND_PID=$!
disown "$BACKEND_PID" 2>/dev/null || true

sleep 2

# Check Backend Health
if curl -s --max-time 5 "http://127.0.0.1:$BACKEND_PORT/health" | grep -q "healthy"; then
    print_status "success" "Backend Server activo (modo desarrollo --reload): http://localhost:$BACKEND_PORT"
else
    print_status "warning" "Backend iniciando en segundo plano..."
fi

# 2. Start Frontend Server
echo ""
print_status "info" "Iniciando Frontend Server en modo desarrollo (Vite)..."

if port_in_use "$FRONTEND_PORT"; then
    print_status "warning" "Puerto $FRONTEND_PORT ocupado (puede ser otro servicio/docker). Buscando puerto libre..."
    pkill -f "vite" 2>/dev/null || true
    sleep 1
fi

cd "$FRONTEND_DIR"
if command -v setsid &>/dev/null; then
    setsid npx vite --port "$FRONTEND_PORT" --host < /dev/null > "$FRONTEND_DIR/vite.log" 2>&1 &
else
    nohup npx vite --port "$FRONTEND_PORT" --host < /dev/null > "$FRONTEND_DIR/vite.log" 2>&1 &
fi
FRONTEND_PID=$!
disown "$FRONTEND_PID" 2>/dev/null || true

sleep 2

ACTUAL_FRONTEND_PORT=$(grep -oE "http://localhost:[0-9]+" "$FRONTEND_DIR/vite.log" | tail -n1 | cut -d':' -f3 || true)
if [[ -z "$ACTUAL_FRONTEND_PORT" ]]; then
    ACTUAL_FRONTEND_PORT="$FRONTEND_PORT"
fi

print_status "success" "Frontend Server activo (Vite HMR): http://localhost:$ACTUAL_FRONTEND_PORT (PID: $FRONTEND_PID)"

echo -e "\n${GREEN}╭──────────────────────────────────────────────────────────╮${NC}"
echo -e "${GREEN}│${NC} ${GREEN}✨ TODOS LOS SERVICIOS ESTÁN EN EJECUCIÓN (MODO DEV)${NC}       ${GREEN}│${NC}"
echo -e "${GREEN}├──────────────────────────────────────────────────────────┤${NC}"
echo -e "${GREEN}│${NC} 🌐 Frontend Web Studio: ${YELLOW}http://localhost:$ACTUAL_FRONTEND_PORT${NC}"
echo -e "${GREEN}│${NC} ⚙️  Backend REST API:    ${YELLOW}http://localhost:$BACKEND_PORT${NC} (con --reload)"
echo -e "${GREEN}│${NC} 🧠 LLM llama-server:   ${YELLOW}http://localhost:${LLAMA_PORT:-1234}${NC}"
echo -e "${GREEN}╰──────────────────────────────────────────────────────────╯${NC}\n"

# If launched in daemon mode, exit cleanly
if [[ "$1" == "--daemon" || "$1" == "-d" ]]; then
    echo "Servicios corriendo en segundo plano. Usa './start-all.sh stop' o 'ai services stop' para detenerlos."
    exit 0
fi

# Interactive mode trap
cleanup() {
    echo -e "\n${YELLOW}⚠ Deteniendo servicios AI-CLI...${NC}"
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    pkill -f "uvicorn server:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    print_status "success" "Servicios detenidos correctamente."
    exit 0
}

trap cleanup INT TERM

echo -e "${BLUE}ℹ Presiona Ctrl+C para detener ambos servicios.${NC}\n"
while true; do
    sleep 2
done
