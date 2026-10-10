#!/usr/bin/env python3
"""
Download the models requested for ai-cli:
1. Ling 3.0 tiny Q4KM (bartowski/Ling-3.0-tiny-GGUF)
2. Gemma 4 E4B Q4KM (unsloth/gemma-4-E4B-it-GGUF)
3. Gemma 4 E2B Q4KM (unsloth/gemma-4-E2B-it-GGUF)
4. PrismML-ternary Bonsai 2 27B PTQ1_0 (prism-ml/Ternary-Bonsai-2-27B-gguf)
"""

import os
import sys
import time
from pathlib import Path
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODELS = [
    {
        "name": "Gemma 4 E2B Q4_K_M",
        "url": "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf",
        "folder": "gemma-4-E2B-it-GGUF",
        "file": "gemma-4-E2B-it-Q4_K_M.gguf",
        "expected_gb": 2.89,
    },
    {
        "name": "Ling 3.0 tiny Q4_K_M",
        "url": "https://huggingface.co/bartowski/Ling-3.0-tiny-GGUF/resolve/main/Ling-3.0-tiny-Q4_K_M.gguf",
        "folder": "Ling-3.0-tiny-GGUF",
        "file": "Ling-3.0-tiny-Q4_K_M.gguf",
        "expected_gb": 4.58,
    },
    {
        "name": "Gemma 4 E4B Q4_K_M",
        "url": "https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q4_K_M.gguf",
        "folder": "gemma-4-E4B-it-GGUF",
        "file": "gemma-4-E4B-it-Q4_K_M.gguf",
        "expected_gb": 4.64,
    },
    {
        "name": "Ternary Bonsai 2 27B (PrismML PTQ1_0)",
        "url": "https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/resolve/main/Ternary-Bonsai-2-27B-PTQ1_0.gguf",
        "folder": "Ternary-Bonsai-2-27B-gguf",
        "file": "Ternary-Bonsai-2-27B-PTQ1_0.gguf",
        "expected_gb": 5.54,
    },
]

def download_file_with_resume(url: str, dest_path: Path, model_name: str) -> bool:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    part_path = dest_path.with_suffix(dest_path.suffix + ".part")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    existing_bytes = 0
    if part_path.exists():
        existing_bytes = part_path.stat().st_size
        headers["Range"] = f"bytes={existing_bytes}-"

    print(f"\n{'='*70}")
    print(f"📦 [Iniciando descarga] {model_name}")
    print(f"   URL: {url}")
    print(f"   Destino: {dest_path}")
    print(f"{'='*70}")

    try:
        with requests.get(url, stream=True, headers=headers, timeout=30, allow_redirects=True) as resp:
            if resp.status_code == 416: # Range not satisfiable (already completed)
                part_path.rename(dest_path)
                print(f"✅ Ya descargado completamente: {dest_path}")
                return True
            
            resp.raise_for_status()

            # Handle total length
            content_range = resp.headers.get("content-range")
            if content_range:
                total_bytes = int(content_range.split("/")[-1])
            else:
                total_bytes = existing_bytes + int(resp.headers.get("content-length", 0))

            mode = "ab" if existing_bytes > 0 and resp.status_code == 206 else "wb"
            if mode == "wb":
                existing_bytes = 0

            downloaded = existing_bytes
            t0 = time.time()
            last_print = 0

            with open(part_path, mode) as f:
                for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last_print > 1.0 or downloaded == total_bytes:
                            last_print = now
                            elapsed = now - t0 if now > t0 else 1
                            speed_mb = (downloaded - existing_bytes) / elapsed / (1024 * 1024)
                            pct = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
                            downloaded_gb = downloaded / (1024 * 1024 * 1024)
                            total_gb = total_bytes / (1024 * 1024 * 1024)
                            print(f"\r  Progreso: {pct:5.1f}% [{downloaded_gb:.2f}/{total_gb:.2f} GB] a {speed_mb:.1f} MB/s", end="", flush=True)

        if part_path.exists():
            part_path.rename(dest_path)
            print(f"\n✅ Completado con éxito: {dest_path.name} ({dest_path.stat().st_size / (1024*1024*1024):.2f} GB)")
            return True

    except Exception as e:
        print(f"\n❌ Error al descargar {model_name}: {e}")
        return False

def main():
    print("Iniciando cola de descarga para AI-CLI en Windows...")
    success = []
    failed = []

    for item in MODELS:
        dest = PROJECT_ROOT / "models" / item["folder"] / item["file"]
        if dest.exists() and dest.stat().st_size > 100 * 1024 * 1024:
            print(f"\n⚡ Modelo ya presente en disco: {item['name']} ({dest.stat().st_size / (1024*1024*1024):.2f} GB)")
            success.append(item["name"])
            continue

        ok = download_file_with_resume(item["url"], dest, item["name"])
        if ok:
            success.append(item["name"])
        else:
            failed.append(item["name"])

    print(f"\n{'='*70}")
    print("📋 RESUMEN DE DESCARGAS:")
    print(f"  ✓ Modelos listos: {len(success)}/{len(MODELS)}")
    for s in success:
        print(f"    - {s}")
    if failed:
        print(f"  ❌ Fallaron: {len(failed)}")
        for f in failed:
            print(f"    - {f}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
