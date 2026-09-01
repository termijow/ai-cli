#!/bin/bash
# Chat history integration for Qwen Code and AI-CLI
# Automatically synchronizes sessions, tokens, and savings

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ -f "$PROJECT_ROOT/bin/ai-sync-savings.py" ]]; then
    python3 "$PROJECT_ROOT/bin/ai-sync-savings.py" "$@"
elif [[ -f "$HOME/Documents/ai-cli/bin/ai-sync-savings.py" ]]; then
    python3 "$HOME/Documents/ai-cli/bin/ai-sync-savings.py" "$@"
fi
