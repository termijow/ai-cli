#!/bin/bash
# AI-CLI Pre-launch Hook
# Ejecutar antes de cada sesión de chat con llama.cpp/Qwen

LAUNCHER_SCRIPT="$HOME/.qwen/bin/chat-launcher.sh"
if [[ -f "$LAUNCHER_SCRIPT" ]]; then
    "$LAUNCHER_SCRIPT"
fi
