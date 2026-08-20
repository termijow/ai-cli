#!/bin/bash
# AI-CLI Services Startup Script
# Starts all backend services for the AI-CLI application

set -e

echo "🚀 Starting AI-CLI Services..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=${BACKEND_PORT:-3094}
BACKEND_HOST=${BACKEND_HOST:-0.0.0.0}

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "warning")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        "info")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
        "error")
            echo -e "${RED}✗${NC} $message"
            exit 1
            ;;
    esac
}

# Function to check if port is in use
port_in_use() {
    local port=$1
    if command -v ss &> /dev/null; then
        ss -tln | grep -q ":$port "
    elif command -v netstat &> /dev/null; then
        netstat -tln | grep -q ":$port "
    elif command -v lsof &> /dev/null; then
        lsof -i -P -n | grep -q ":$port"
    else
        return 1
    fi
}

# Function to wait for port to be available
wait_for_port() {
    local port=$1
    local max_attempts=30
    local attempt=1
    while port_in_use $port && [ $attempt -le $max_attempts ]; do
        print_status "warning" "Port $port is in use, waiting..."
        sleep 2
        ((attempt++))
    done
    if port_in_use $port; then
        print_status "error" "Failed to release port $port after $((max_attempts * 2)) seconds"
        exit 1
    fi
}

# Function to check if service is running
is_service_running() {
    local port=$1
    local service=$2
    if port_in_use $port; then
        # Check if the specific service is responding
        if curl -s --max-time 5 "http://localhost:$port/${service}/health" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Start backend server
echo ""
print_status "info" "Starting Backend Server..."
wait_for_port $BACKEND_PORT

cd /home/termihoe/Documents/ai-cli/backend
nohup /home/termihoe/Documents/ai-cli/venv/bin/python -m uvicorn server:app --host $BACKEND_HOST --port $BACKEND_PORT --log-level info > /home/termihoe/Documents/ai-cli/backend/server.log 2>&1 &

sleep 3

# Check if backend started successfully
if is_service_running $BACKEND_PORT "health"; then
    print_status "success" "Backend Server started on http://$BACKEND_HOST:$BACKEND_PORT"
else
    print_status "error" "Backend Server failed to start"
    exit 1
fi

# Start frontend server
echo ""
print_status "info" "Starting Frontend Server..."
cd /home/termihoe/Documents/ai-cli/frontend
FRONTEND_PORT=${FRONTEND_PORT:-5173} node scripts/start.js &

sleep 2

print_status "success" "Frontend Server started on http://localhost:$FRONTEND_PORT"

# Check for additional services to start
# TODO: Add more services as needed

echo ""
print_status "success" "All services started successfully!"
echo ""
echo "Services:"
echo "  - Backend Server: http://localhost:$BACKEND_PORT"
echo "  - Frontend Server: http://localhost:$FRONTEND_PORT"
echo "  - (Add more services as needed)"
echo ""
print_status "info" "Services running. Press Ctrl+C to stop all services."

# Trap to clean up on exit
trap 'echo ""; print_status "warning" "Shutting down services..."; pkill -f "uvicorn server:app" 2>/dev/null || true; pkill -f "node scripts/start.js" 2>/dev/null || true; exit 0' INT TERM
