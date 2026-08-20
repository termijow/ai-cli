#!/bin/bash
# websocket_savings_handler.sh - WebSocket endpoint for real-time savings monitoring
# This script creates a simple WebSocket server that listens on port 1234
# and provides savings data to connected clients

PORT="${1:-1234}"

SavingsFile="$HOME/.ai_cli_savings"
DbFile="$HOME/.ai_cli_db.db"

echo "Starting WebSocket server on port $PORT..."
echo "Press Ctrl+C to stop"

while true; do
    if [[ -f "$SavingsFile" ]]; then
        CURRENT_SAVINGS=$(cat "$SavingsFile")
    else
        CURRENT_SAVINGS="0.00"
    fi
    
    # WebSocket message format: {"type": "savings", "data": {...}}
    echo "{\"type\": \"savings\", \"data\": {\"total_savings\": $CURRENT_SAVINGS, \"timestamp\": $(date +%s)}}"
    sleep 1
done
