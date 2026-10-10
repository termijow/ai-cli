#!/usr/bin/env python3
# ==============================================================================
# AI-CLI ARENA: LLM TOURNAMENT & BENCHMARK HARNESS
# ==============================================================================
import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

# Configurar encoding UTF-8 en terminales de Windows
try:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Configuración y Rutas
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"
PRESETS_DIR = PROJECT_ROOT / "presets"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "arena"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LLAMA_BIN = PROJECT_ROOT / "llama-bin" / "llama-server.exe"
LLAMA_PRISM = PROJECT_ROOT / "llama-prism" / "llama-server.exe"

# Reglas del Torneo Estandarizado
STANDARD_THINKING_BUDGET = 8192
STANDARD_MAX_TOKENS = 16384
MAX_TEST_TOKEN_BUDGET = 100000

BENCHMARK_PROMPT = """Eres un ingeniero de software senior y desarrollador experto en videojuegos web.
Tu tarea es programar un juego arcade retro Snake (la viborita) en un ÚNICO archivo HTML autocontenido (HTML + CSS embebido + JavaScript sin dependencias externas).

Requisitos obligatorios:
1. Gráficos en Canvas 2D con estética retro cyberpunk o arcade oscura (colores neón, rejilla tenue, serpiente con gradiente/brillo).
2. Bucle de juego fluido a velocidad constante (10-14 ticks por segundo).
3. Controles: Teclado (Flechas y WASD) y controles táctiles en pantalla (D-Pad táctil responsivo para móvil).
4. Mecánicas: Sistema de puntuación actual y récord (High Score) persistido en localStorage.
5. Efectos: Efecto de partículas cuando come manzana, vibración/screen shake ligero al morir, y sonidos sintetizados con la Web Audio API (sin audios externos ni librerías).
6. Pantalla de Game Over con botón de reinicio y botón de pausa.
7. Cero placeholders, cero comentarios como '// el resto aquí'. Entrega el código 100% completo y funcional listo para abrir en el navegador.

Formato de salida:
Entrega únicamente el bloque con el código del archivo HTML completo.
"""

def colorize(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def c_blue(t): return colorize(t, "1;34")
def c_green(t): return colorize(t, "1;32")
def c_yellow(t): return colorize(t, "1;33")
def c_cyan(t): return colorize(t, "1;36")
def c_red(t): return colorize(t, "1;31")
def c_bold(t): return colorize(t, "1")

def find_available_models():
    found = []
    if not MODELS_DIR.exists():
        return found
    for f in MODELS_DIR.rglob("*.gguf"):
        # Ignorar archivos auxiliares mmproj o imatrix
        if "mmproj" in f.name.lower() or "imatrix" in f.name.lower():
            continue
        found.append(f)
    return sorted(found, key=lambda x: x.name)

def kill_server():
    subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

def wait_for_server(port=1234, timeout=45):
    start = time.time()
    url = f"http://127.0.0.1:{port}/health"
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False

def load_preset_for_model(model_name):
    # Buscar preset por coincidencia
    stem = model_name.replace(".gguf", "")
    candidates = [
        PRESETS_DIR / f"{stem}.conf",
        PRESETS_DIR / f"{model_name}.conf"
    ]
    for c in candidates:
        if c.exists():
            return parse_preset_file(c)
    
    # Búsqueda por glob heurístico
    if "gemma-4-26b" in stem.lower():
        p = list(PRESETS_DIR.glob("*gemma-4-26B*.conf"))
        if p: return parse_preset_file(p[0])
    elif "gemma-4-e4b" in stem.lower():
        p = list(PRESETS_DIR.glob("*gemma-4-E4B*.conf"))
        if p: return parse_preset_file(p[0])
    elif "ling-3" in stem.lower():
        p = list(PRESETS_DIR.glob("*Ling-3.0*.conf"))
        if p: return parse_preset_file(p[0])
    elif "qwen3.6-35b" in stem.lower():
        p = list(PRESETS_DIR.glob("*Qwen3.6-35B*.conf"))
        if p: return parse_preset_file(p[0])
    elif "qwen3.5-9b" in stem.lower():
        p = list(PRESETS_DIR.glob("*Qwen3.5-9B*.conf"))
        if p: return parse_preset_file(p[0])
    elif "bonsai" in stem.lower() or "ternary" in stem.lower():
        p = list(PRESETS_DIR.glob("*Ternary-Bonsai*.conf"))
        if p: return parse_preset_file(p[0])

    return {}

def parse_preset_file(path):
    data = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
    return data

def start_server_for_model(model_path):
    kill_server()
    name = model_path.name
    preset = load_preset_for_model(name)

    is_prism = any(x in name.lower() for x in ["ternary", "bonsai", "ptq1_0", "pq2_0"])
    exe = LLAMA_PRISM if (is_prism and LLAMA_PRISM.exists()) else LLAMA_BIN

    gpu_layers = preset.get("AI_GPU_LAYERS", "99")
    ctx_size = preset.get("AI_CTX_SIZE", "16384")
    cache_k = preset.get("AI_CACHE_TYPE_K", "q4_0")
    cache_v = preset.get("AI_CACHE_TYPE_V", "q4_0")
    mtp = preset.get("AI_MTP", "off")
    mtp_draft = preset.get("AI_MTP_DRAFT_MAX", "2")

    cmd = [
        str(exe),
        "--model", str(model_path),
        "--host", "127.0.0.1",
        "--port", "1234",
        "--threads", "6",
        "--threads-batch", "6",
        "--n-gpu-layers", str(gpu_layers),
        "--ctx-size", str(ctx_size),
        "--batch-size", "1024",
        "--ubatch-size", "256",
        "--device", "Vulkan0",
        "--jinja",
        "--flash-attn", "auto",
        "--parallel", "1",
        "--cache-ram", "4096",
        "--cache-type-k", cache_k,
        "--cache-type-v", cache_v,
        "--alias", "localmodel",
        "--reasoning", "on",
        "--reasoning-budget", str(STANDARD_THINKING_BUDGET),
        "--reasoning-format", "none",
        "--predict", str(STANDARD_MAX_TOKENS)
    ]

    if mtp == "on" or "mtp" in name.lower():
        cmd.extend(["--spec-type", "draft-mtp", "--spec-draft-n-max", str(mtp_draft)])

    # Lanzar proceso en segundo plano oculto
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )

    if not wait_for_server(port=1234, timeout=40):
        return False, "El servidor no respondió a tiempo."
    return True, preset

def evaluate_code(code_str):
    score = 0
    details = []

    if "<!DOCTYPE html>" in code_str or "<html" in code_str:
        score += 15
        details.append("Estructura HTML básica (+15)")
    if "<canvas" in code_str:
        score += 20
        details.append("Canvas 2D presente (+20)")
    if "requestAnimationFrame" in code_str or "setInterval" in code_str:
        score += 15
        details.append("Game Loop estándar (+15)")
    if "AudioContext" in code_str or "webkitAudioContext" in code_str:
        score += 15
        details.append("Web Audio API sintetizada (+15)")
    if "localStorage" in code_str:
        score += 10
        details.append("High Score persistente (+10)")
    if "touchstart" in code_str or "touch" in code_str.lower() or "dpad" in code_str.lower():
        score += 15
        details.append("Controles táctiles / D-Pad (+15)")
    if len(code_str) > 2000 and "TODO" not in code_str:
        score += 10
        details.append("Código autocontenido y completo (+10)")

    return min(score, 100), details

def run_benchmark_on_model(model_path):
    model_name = model_path.name
    print(c_cyan(f"\n========================================================"))
    print(c_yellow(f"🚀 INICIANDO BENCHMARK ARENA: {model_name}"))
    print(c_cyan(f"========================================================"))
    print(f"📦 Tamaño: {model_path.stat().st_size / (1024**3):.2f} GB")
    print(f"🧠 Thinking Budget: {STANDARD_THINKING_BUDGET} tokens")
    print(f"📤 Ventana Max Output: {STANDARD_MAX_TOKENS} tokens")
    print(f"🎯 Límite Total de Sesión: {MAX_TEST_TOKEN_BUDGET} tokens")

    print(c_blue("\n✦ Levantando llama-server con aceleración Vulkan y preset calibrado..."))
    ok, preset_info = start_server_for_model(model_path)
    if not ok:
        print(c_red(f"❌ Error al iniciar servidor: {preset_info}"))
        return None

    print(c_green("✓ Servidor listo. Enviando prompt estandarizado (Snake Game)..."))
    
    url = "http://127.0.0.1:1234/v1/chat/completions"
    payload = {
        "model": "localmodel",
        "messages": [
            {"role": "system", "content": "Eres un ingeniero de software senior. Genera código limpio, autocontenido y funcional sin texto conversacional."},
            {"role": "user", "content": BENCHMARK_PROMPT}
        ],
        "temperature": 0.2,
        "max_tokens": STANDARD_MAX_TOKENS,
        "stream": True
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    t0 = time.time()
    first_token_time = None
    accumulated_content = []
    accumulated_thought = []
    in_thought = False
    prompt_tokens = 0
    completion_tokens = 0

    print(c_yellow("\n✦ Generando respuesta en streaming..."))
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line or not line.startswith("data: "): continue
                data_str = line[6:]
                if data_str == "[DONE]": break
                try:
                    chunk = json.loads(data_str)
                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    
                    if first_token_time is None:
                        first_token_time = time.time()
                    
                    # Detectar pensamiento vs contenido
                    thought = delta.get("reasoning_content") or delta.get("thought")
                    content = delta.get("content", "")

                    if thought:
                        accumulated_thought.append(thought)
                        print(colorize(".", "0;33"), end="", flush=True)
                    elif content:
                        accumulated_content.append(content)
                        print(colorize(".", "0;32"), end="", flush=True)

                    completion_tokens += 1
                except Exception:
                    continue

    except Exception as e:
        print(c_red(f"\n❌ Error durante streaming: {e}"))
        return None

    t_total = time.time() - t0
    ttft = (first_token_time - t0) if first_token_time else 0.0
    tok_sec = completion_tokens / t_total if t_total > 0 else 0.0

    print(f"\n\n{c_green('✓ Generación completada con éxito!')}")
    print(f"⏱ Tiempo total: {t_total:.2f} s | TTFT: {ttft:.2f} s")
    print(f"⚡ Velocidad media: {c_bold(f'{tok_sec:.2f} tok/s')}")
    print(f"📊 Tokens generados: {completion_tokens} (Pensamiento: {len(accumulated_thought)} | Código: {len(accumulated_content)})")

    full_output = "".join(accumulated_content)
    # Extraer bloque HTML
    match = re.search(r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?|<html[\s\S]*?)```", full_output, re.IGNORECASE)
    if match:
        html_code = match.group(1).strip()
    else:
        # Si no vino en bloque markdown, buscar <html> directamente
        html_match = re.search(r"(<!DOCTYPE html[\s\S]*?</html>|<html[\s\S]*?</html>)", full_output, re.IGNORECASE)
        html_code = html_match.group(1).strip() if html_match else full_output.strip()

    # Evaluar calidad de código
    score, details = evaluate_code(html_code)

    # Guardar archivo generado
    model_safe_dir = RESULTS_DIR / model_name.replace(".gguf", "")
    model_safe_dir.mkdir(parents=True, exist_ok=True)
    out_file = model_safe_dir / "snake.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_code)

    print(f"💾 Archivo guardado en: {c_cyan(str(out_file))}")
    print(f"🏆 Puntuación de Calidad: {c_yellow(f'{score}/100')}")
    for d in details:
        print(f"   ├─ {d}")

    return {
        "model": model_name,
        "size_gb": model_path.stat().st_size / (1024**3),
        "tokens": completion_tokens,
        "time_s": t_total,
        "speed": tok_sec,
        "score": score,
        "out_file": str(out_file)
    }

def print_and_save_leaderboard(results):
    if not results: return
    # Ordenar por Score y luego por Velocidad
    results.sort(key=lambda x: (x["score"], x["speed"]), reverse=True)

    header = f"\n{c_blue('╔══════════════════════════════════════════════════════════════════════════════════════╗')}\n"
    header += f"{c_blue('║')} {c_yellow('🏆 LEADERBOARD ARENA DE MODELOS LOCALES (SNAKE BENCHMARK)')}                    {c_blue('║')}\n"
    header += f"{c_blue('╠══════════════════════════════════════════════════════════════════════════════════════╣')}\n"
    print(header, end="")

    print(f"{'Pos':<4} | {'Modelo':<32} | {'Velocidad':<11} | {'Tiempo':<9} | {'Tokens':<8} | {'Calidad':<8}")
    print("-" * 88)

    md_lines = [
        "# 🏆 Leaderboard Arena de Modelos Locales (Snake Benchmark)",
        "",
        "| Pos | Modelo | Tamaño | Velocidad | Tiempo Total | Tokens | Puntuación | Archivo Generado |",
        "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|"
    ]

    for idx, r in enumerate(results, 1):
        m_short = r["model"][:30]
        speed_str = f"{r['speed']:.2f} t/s"
        time_str = f"{r['time_s']:.1f} s"
        score_str = f"{r['score']}/100"
        
        print(f"{idx:<4} | {m_short:<32} | {c_green(speed_str):<20} | {time_str:<9} | {r['tokens']:<8} | {c_yellow(score_str):<16}")
        
        rel_path = f"benchmarks/arena/{Path(r['out_file']).parent.name}/snake.html"
        md_lines.append(f"| {idx} | **{r['model']}** | {r['size_gb']:.2f} GB | **{speed_str}** | {time_str} | {r['tokens']} | **{score_str}** | [{Path(r['out_file']).name}]({rel_path}) |")

    print(c_blue("╚══════════════════════════════════════════════════════════════════════════════════════╝\n"))

    md_file = RESULTS_DIR / "LEADERBOARD.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(c_green(f"📊 Tabla guardada en Markdown: {md_file}"))

def main():
    print(c_blue("╭──────────────────────────────────────────────────────────╮"))
    print(c_blue("│") + c_yellow(" ⚔️  AI-CLI ARENA: TORNEO DE MODELOS & BENCHMARK HARNESS ") + c_blue("│"))
    print(c_blue("╰──────────────────────────────────────────────────────────╯"))

    models = find_available_models()
    if not models:
        print(c_red("❌ No se encontraron modelos en la carpeta models/"))
        sys.exit(1)

    print("\n📦 Modelos disponibles en tu máquina:")
    for idx, m in enumerate(models, 1):
        sz = m.stat().st_size / (1024**3)
        print(f"  {idx}) {c_bold(m.name)} ({sz:.2f} GB)")

    print(f"  {c_green('A) Correr TODOS en modo Torneo Automático (Full Arena)')}")
    print(f"  0) Salir")

    opt = input("\nElige una opción [A, 1-N, 0]: ").strip()
    if opt == "0" or not opt:
        sys.exit(0)

    selected_models = []
    if opt.lower() == "a":
        selected_models = models
    elif opt.isdigit() and 1 <= int(opt) <= len(models):
        selected_models = [models[int(opt) - 1]]
    else:
        print(c_red("Opción inválida."))
        sys.exit(1)

    results = []
    for m in selected_models:
        res = run_benchmark_on_model(m)
        if res:
            results.append(res)

    print_and_save_leaderboard(results)

if __name__ == "__main__":
    main()
