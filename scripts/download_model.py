#!/usr/bin/env python3
"""Download Qwen3.5-9B-GGUF model from Hugging Face."""

import sys
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_URL = "https://huggingface.co/Qwen/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-GGUF.Q4_K_M.gguf"
MODEL_DIR = PROJECT_ROOT / "models" / "Qwen3.5-9B-GGUF"
MODEL_PATH = MODEL_DIR / "Qwen3.5-9B-GGUF.Q4_K_M.gguf"


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {MODEL_URL}...")
    print(f"Destination: {MODEL_PATH}")
    
    with open(MODEL_PATH, "wb") as f:
        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()
        total_len = response.headers.get('content-length')
        downloaded = 0
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_len:
                    pct = (downloaded / int(total_len)) * 100
                    print(f"\rProgress: {pct:.1f}% ({downloaded / (1024*1024):.1f} MB)", end="", flush=True)

    print(f"\nSaved to: {MODEL_PATH}")
    print(f"File size: {MODEL_PATH.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
