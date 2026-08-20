#!/usr/bin/env python3
"""Download Qwen3.5-9B-GGUF model from Hugging Face."""

import requests
from pathlib import Path

MODEL_URL = "https://huggingface.co/Qwen/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-GGUF.Q4_K_M.gguf"
MODEL_PATH = Path("/home/termihoe/Documents/ai-cli/models/Qwen3.5-9B-GGUF/Qwen3.5-9B-GGUF.Q4_K_M.gguf")
MODEL_DIR = MODEL_PATH.parent

def main():
    # Create directory if it doesn't exist
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download the model file
    print(f"Downloading {MODEL_URL}...")
    with open(MODEL_PATH, "wb") as f:
        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Saved to: {MODEL_PATH}")
    print(f"File size: {MODEL_PATH.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()
