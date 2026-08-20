#!/bin/bash
# Wrapper para llama.cpp con hook de pre-carga

# Ejecutar pre-launch hook
/bin/bash "$HOME/.qwen/bin/ai-pre-launch.sh"

# Ejecutar llama.cpp normalmente
exec "$@"
