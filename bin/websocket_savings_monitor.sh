#!/bin/bash
# websocket_savings_monitor.sh - WebSocket endpoint for real-time savings monitoring
# Starts the Python WebSocket server and runs the token counter in parallel

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start websocket server in background
python3 "$SCRIPT_DIR/websocket_savings_handler.py" &
SERVER_PID=$!
echo "WebSocket server started with PID: $SERVER_PID"

# Wait for server to start
sleep 1

# Start token counter in background, reading from websocket server
"$SCRIPT_DIR/token_counter.sh" < <(python3 "$SCRIPT_DIR/websocket_savings_handler.py" | tee /dev/tty) &
COUNTER_PID=$!
echo "Token counter started with PID: $COUNTER_PID"

# Keep both running until interrupted
echo "Both processes running. Press Ctrl+C to stop everything."

# Cleanup on exit
cleanup() {
    echo "Cleaning up..."
    kill $COUNTER_PID 2>/dev/null
    kill $SERVER_PID 2>/dev/null
    wait 2>/dev/null
    echo "Stopped."
}

trap cleanup EXIT INT TERM

# Wait for counter to finish
wait $COUNTER_PID 2>/dev/null
echo "Token counter finished."
exit 0
