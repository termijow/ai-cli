#!/bin/bash

# Function to install the model
install_model() {
    local url="$1"
    local model_name=$(basename "$url" .gguf)
    local model_repo=$(dirname "$url")

    # Download the model
    curl -L -O "$url"
    if [ $? -ne 0 ]; then
        echo "Error: Download failed"
        rm -f "$model_name.gguf"
        exit 1
    fi

    # Move the model to the models directory
    mkdir -p ~/models
    mv "$model_name.gguf" ~/models/

    # Update .env file
    sed -i "s/^MODEL_FILE=.*/MODEL_FILE=$model_name.gguf/" ~/.env
    sed -i "s/^MODEL_REPO=.*/MODEL_REPO=$model_repo/" ~/.env

    # Restart the server
    ./bin/ai-serve
    if [ $? -ne 0 ]; then
        echo "Error: Server restart failed"
        exit 1
    fi

    echo "✅ Modelo instalado y configurado. Reiniciando servidor..."
}

# Execute the install_model function with the URL provided as an argument
install_model "$1"