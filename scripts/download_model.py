#!/usr/bin/env python3
"""Download GGUF models from Hugging Face for ai-cli."""

import sys
import argparse
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_URL = "https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-Q4_K_M.gguf?download=true"
DEFAULT_DIR = PROJECT_ROOT / "models" / "Qwen3.5-0.8B-GGUF"
DEFAULT_PATH = DEFAULT_DIR / "Qwen3.5-0.8B-Q4_K_M.gguf"


def download_model(url: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {url}...")
    print(f"Destination: {output_path}")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    with requests.get(url, stream=True, headers=headers, allow_redirects=True) as response:
        response.raise_for_status()
        total_len = response.headers.get('content-length')
        downloaded = 0
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_len:
                        pct = (downloaded / int(total_len)) * 100
                        print(f"\rProgress: {pct:.1f}% ({downloaded / (1024*1024):.1f} MB)", end="", flush=True)

    print(f"\nSaved to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description="Download GGUF model for ai-cli")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="Model download URL")
    parser.add_argument("-o", "--output", help="Destination file path")
    args = parser.parse_args()

    if args.output:
        out_path = Path(args.output).resolve()
    else:
        # Extract filename from URL
        clean_url = args.url.split("?")[0]
        filename = clean_url.split("/")[-1]
        model_name = clean_url.split("/")[-3] if len(clean_url.split("/")) >= 3 else "models"
        out_dir = PROJECT_ROOT / "models" / model_name
        out_path = out_dir / filename

    download_model(args.url, out_path)


if __name__ == "__main__":
    main()
