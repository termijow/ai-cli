#!/usr/bin/env python3
"""
master.py - AI-CLI Master Service Orchestrator
Cross-platform manager for Backend (FastAPI :3094), Frontend (Vite :5173 / Static), and LLM Server (:1234).
Works 100% natively on Windows, Linux, and macOS without breaking Docker or Linux setups.
"""

import sys
import os
import subprocess
import time
import socket
import argparse
from pathlib import Path

# Configurar salida UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"

# Localizar intérprete de Python preferido (venv o sistema)
if IS_WINDOWS:
    PYTHON_BIN = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
else:
    PYTHON_BIN = PROJECT_ROOT / "venv" / "bin" / "python"

if not PYTHON_BIN.exists():
    PYTHON_BIN = Path(sys.executable)

# Localizar npm
NPM_CMD = "npm.cmd" if IS_WINDOWS else "npm"


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


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def get_frontend_port() -> int:
    for p in [5173, 5174, 5175]:
        if is_port_open(p):
            return p
    # Si backend está activo y frontend dist existe, el puerto es 3094
    if is_port_open(3094):
        return 3094
    return 5173


def kill_port(port: int):
    """Cierra limpiamente cualquier proceso escuchando en un puerto específico de forma multiplataforma."""
    if IS_WINDOWS:
        try:
            cmd = f'netstat -ano | findstr :{port}'
            out = subprocess.check_output(cmd, shell=True, errors="ignore")
            killed_pids = set()
            for line in out.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = parts[-1]
                    if pid.isdigit() and pid not in killed_pids and pid != "0":
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        killed_pids.add(pid)
        except Exception:
            pass
    else:
        subprocess.run(["fuser", "-k", f"{port}/tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_services():
    print_colored("warning", "🛑 Deteniendo servicios AI-CLI...")

    if IS_WINDOWS:
        # Detener puertos específicos en Windows
        kill_port(3094)
        kill_port(5173)
        kill_port(5174)
        # Detener cualquier proceso de uvicorn residual
        subprocess.run('taskkill /F /IM uvicorn.exe >nul 2>&1', shell=True)
    else:
        # Comandos limpios para Linux y macOS
        subprocess.run(["pkill", "-f", "uvicorn server:app"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "vite"], stderr=subprocess.DEVNULL)
        kill_port(3094)
        kill_port(5173)

        # Si hay contenedores Docker levantados en Linux, detenerlos también
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        if compose_file.exists():
            subprocess.run(["docker", "compose", "-f", str(compose_file), "down"], stderr=subprocess.DEVNULL)

    time.sleep(1)
    print_colored("success", "✓ Servicios Backend y Frontend detenidos correctamente.")


def status_services():
    print_colored("info", "\n🔍 Estado de los Servicios AI-CLI:")

    backend_up = is_port_open(3094)
    vite_up = is_port_open(5173) or is_port_open(5174)
    llm_up = is_port_open(1234)

    os_label = "Windows (Nativo)" if IS_WINDOWS else ("macOS (Nativo)" if IS_MACOS else "Linux")
    print(f"  • Sistema Operativo:   {os_label}")
    
    if vite_up:
        f_port = 5174 if is_port_open(5174) else 5173
        print(f"  • Frontend Web (Dev)   (:{f_port}): 🟢 ONLINE (http://localhost:{f_port})")
    elif backend_up:
        print(f"  • Frontend Web Studio  (:3094): 🟢 ONLINE (http://localhost:3094/) [Embebido]")
    else:
        print(f"  • Frontend Web Studio  (:5173/:3094): 🔴 OFFLINE")

    print(f"  • Backend REST API     (:3094): {'🟢 ONLINE (http://localhost:3094)' if backend_up else '🔴 OFFLINE'}")
    print(f"  • Arena Benchmarks UI  (:3094): {'🟢 ONLINE (http://localhost:3094/benchmarks)' if backend_up else '🔴 OFFLINE'}")
    print(f"  • LLM llama-server     (:1234): {'🟢 ONLINE (http://localhost:1234)' if llm_up else '🔴 OFFLINE (Inicia con: ai serve)'}")
    print()


def start_native_services(daemon: bool = True):
    print_colored("info", f"🚀 Iniciando servicios AI-CLI en modo Nativo ({'Windows' if IS_WINDOWS else 'Unix'})...")

    # 1. Iniciar Backend (FastAPI en :3094)
    backend_script = PROJECT_ROOT / "backend" / "server.py"
    if not is_port_open(3094):
        print(f"✦ Levantando Backend FastAPI (:3094)...")
        backend_log = open(LOGS_DIR / "backend.log", "w", encoding="utf-8", errors="replace")
        
        env = dict(os.environ)
        backend_dir = str(PROJECT_ROOT / "backend")
        env["PYTHONPATH"] = f"{backend_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

        creationflags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if (IS_WINDOWS and daemon) else (subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0)
        
        backend_proc = subprocess.Popen(
            [str(PYTHON_BIN), str(backend_script)],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=backend_log,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            close_fds=True if (IS_WINDOWS and daemon) else False
        )
    else:
        print_colored("success", "✓ Backend ya se encuentra activo en el puerto 3094.")

    # 2. Iniciar Frontend Vite si se desea en modo dev y node_modules existe
    frontend_dir = PROJECT_ROOT / "frontend"
    has_node_modules = (frontend_dir / "node_modules").exists()
    
    if has_node_modules and not is_port_open(5173) and not is_port_open(5174):
        print(f"✦ Levantando Frontend Vite Dev Server (:5173)...")
        frontend_log = open(LOGS_DIR / "frontend.log", "w", encoding="utf-8", errors="replace")
        creationflags = (subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0)
        try:
            subprocess.Popen(
                [NPM_CMD, "run", "dev"],
                cwd=str(frontend_dir),
                stdout=frontend_log,
                stderr=subprocess.STDOUT,
                creationflags=creationflags
            )
        except Exception as e:
            print_colored("warning", f"Nota: Vite dev server no pudo ser iniciado ({e}). Se usará la interfaz estática servida en :3094.")

    # 3. Esperar que el backend responda
    print("✦ Esperando disponibilidad de los servicios...")
    for _ in range(25):
        if is_port_open(3094):
            break
        time.sleep(0.5)

    time.sleep(1)

    # 4. Mostrar resumen con links clicables
    frontend_port = get_frontend_port()
    backend_up = is_port_open(3094)
    llm_up = is_port_open(1234)

    print(f"\n\033[92m╭──────────────────────────────────────────────────────────────╮\033[0m")
    print(f"\033[92m│\033[0m \033[1;32m✨ SERVICIOS AI-CLI ACTIVOS Y LISTOS\033[0m                          \033[92m│\033[0m")
    print(f"\033[92m├──────────────────────────────────────────────────────────────┤\033[0m")
    print(f"\033[92m│\033[0m 🌐 \033[1mWeb Studio:\033[0m        \033[1;33mhttp://localhost:{frontend_port}\033[0m")
    print(f"\033[92m│\033[0m ⚔️  \033[1mArena Benchmarks:\033[0m  \033[1;33mhttp://localhost:3094/benchmarks\033[0m")
    print(f"\033[92m│\033[0m ⚙️  \033[1mBackend REST API:\033[0m  \033[1;33mhttp://localhost:3094\033[0m")
    print(f"\033[92m│\033[0m 🧠 \033[1mLLM llama-server:\033[0m  \033[1;33mhttp://localhost:1234\033[0m {'(🟢 Activo)' if llm_up else '(🔴 Inicia con: ai serve)'}")
    print(f"\033[92m╰──────────────────────────────────────────────────────────────╯\033[0m\n")
    print_colored("info", "💡 Tip: Usa 'ai services stop' para detener los servicios en cualquier momento.")


def open_browser():
    port = get_frontend_port()
    url = f"http://localhost:{port}"
    print(f"✦ Abriendo navegador en: {url}...")
    if IS_WINDOWS:
        os.system(f'start "" "{url}"')
    elif IS_MACOS:
        subprocess.run(["open", url])
    else:
        subprocess.run(["xdg-open", url])


def start_services(daemon=True, force_docker=False):
    # En Linux, si se pide Docker explícitamente y existe docker compose
    if not IS_WINDOWS and force_docker:
        start_script = PROJECT_ROOT / "start-all.sh"
        if start_script.exists():
            args = ["bash", str(start_script)]
            if daemon:
                args.append("--daemon")
            subprocess.run(args, cwd=str(PROJECT_ROOT))
            return

    # Modo Nativo por defecto (ideal para Windows, macOS y Linux sin Docker)
    start_native_services(daemon=daemon)


def main():
    # Ignorar subcomando redundant 'services' o 'service' si se pasa como primer argumento
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["services", "service"]:
        sys.argv.pop(1)

    arg_parser = argparse.ArgumentParser(description="AI-CLI Master Service Orchestrator")
    arg_parser.add_argument("action", nargs="?", default="start", choices=["start", "stop", "restart", "status", "check", "down", "open", "browse", "daemon"])
    arg_parser.add_argument("--daemon", "-d", action="store_true", help="Iniciar en segundo plano")
    arg_parser.add_argument("--docker", action="store_true", help="Forzar ejecución vía Docker Compose (Linux)")
    arg_parser.add_argument("--native", action="store_true", help="Forzar ejecución nativa sin Docker")
    args = arg_parser.parse_args()

    action = args.action

    if action in ["status", "check"]:
        status_services()
    elif action in ["stop", "kill", "down"]:
        stop_services()
    elif action in ["restart"]:
        stop_services()
        time.sleep(1)
        start_services(daemon=True, force_docker=args.docker)
    elif action in ["daemon"]:
        start_services(daemon=True, force_docker=args.docker)
    elif action in ["open", "browse"]:
        open_browser()
    elif action in ["start"]:
        start_services(daemon=True, force_docker=args.docker)
    else:
        print("Uso: ai services [start|stop|restart|status|open]")


if __name__ == "__main__":
    main()
