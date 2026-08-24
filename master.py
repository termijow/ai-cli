#!/usr/bin/env python3
"""
master.py - AI-CLI Master Service Orchestrator
Manages Backend (FastAPI :3094), Frontend (Vite :5173), and LLM Server (:1234).
"""

import sys
import os
import subprocess
import time
import signal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_BIN = PROJECT_ROOT / "venv" / "bin" / "python"
if not PYTHON_BIN.exists():
    PYTHON_BIN = Path(sys.executable)


def print_colored(status: str, message: str):
    colors = {
        "success": "\033[92m",
        "warning": "\033[93m",
        "info": "\033[94m",
        "error": "\033[91m",
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    print(f"{color}{message}{reset}")


def is_port_open(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def get_frontend_port() -> int:
    for p in [5173, 5174, 5175]:
        if is_port_open(p):
            try:
                import urllib.request
                with urllib.request.urlopen(f"http://127.0.0.1:{p}", timeout=0.5) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    if "AI-CLI" in html or "main.jsx" in html:
                        return p
            except Exception:
                pass
    return 5174 if is_port_open(5174) else (5173 if is_port_open(5173) else 5173)


def status_services():
    print_colored("info", "\n🔍 Estado de los Servicios AI-CLI:")
    
    frontend_port = get_frontend_port()
    backend_up = is_port_open(3094)
    frontend_up = is_port_open(frontend_port)
    llm_up = is_port_open(1234)

    print(f"  • Frontend Web Studio (:{frontend_port}): {'🟢 ONLINE (http://localhost:' + str(frontend_port) + ')' if frontend_up else '🔴 OFFLINE'}")
    print(f"  • Backend REST API     (:3094): {'🟢 ONLINE (http://localhost:3094)' if backend_up else '🔴 OFFLINE'}")
    print(f"  • LLM llama-server    (:1234): {'🟢 ONLINE (http://localhost:1234)' if llm_up else '🔴 OFFLINE'}")
    print()


def stop_services():
    print_colored("warning", "🛑 Deteniendo servicios...")
    subprocess.run(["pkill", "-f", "uvicorn server:app"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-f", "vite"], stderr=subprocess.DEVNULL)
    subprocess.run(["fuser", "-k", "3094/tcp"], stderr=subprocess.DEVNULL)
    subprocess.run(["fuser", "-k", "5173/tcp"], stderr=subprocess.DEVNULL)
    print_colored("success", "✓ Backend y Frontend detenidos.")


def start_services(daemon=False):
    print_colored("info", "🚀 Iniciando AI-CLI Services (Backend + Frontend)...")
    start_script = PROJECT_ROOT / "start-all.sh"
    args = ["bash", str(start_script)]
    if daemon:
        args.append("--daemon")
    
    subprocess.run(args, cwd=str(PROJECT_ROOT))


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "start"

    if action in ["status", "check"]:
        status_services()
    elif action in ["stop", "kill", "down"]:
        stop_services()
    elif action in ["restart"]:
        stop_services()
        time.sleep(1)
        start_services()
    elif action in ["daemon", "-d", "--daemon"]:
        start_services(daemon=True)
    elif action in ["start", "up", "all"]:
        start_services()
    else:
        print("Uso: python3 master.py [start|stop|restart|status|daemon]")


if __name__ == "__main__":
    main()
