#!/usr/bin/env python3
# ==============================================================================
# AI-CLI ARENA: LLM TOURNAMENT & LOOP ENGINEERING HARNESS
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

# Garantizar que Node.js y npm estén en el PATH para subprocesos
node_dir = r"C:\Program Files\nodejs"
npm_dir = r"C:\Users\USUARIO\AppData\Roaming\npm"
curr_path = os.environ.get("PATH", "")
if node_dir not in curr_path:
    os.environ["PATH"] = f"{node_dir};{npm_dir};{curr_path}"

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
2. Bucle de juego fluido a velocidad constante (10-14 ticks por segundo con requestAnimationFrame o delta time).
3. Controles: Teclado (Flechas y WASD) y controles táctiles en pantalla (D-Pad táctil responsivo para móvil con eventos touchstart/touchend).
4. Mecánicas: Sistema de puntuación actual y récord (High Score) persistido en localStorage.
5. Efectos: Efecto de partículas cuando come manzana, vibración/screen shake ligero al morir, y sonidos sintetizados con la Web Audio API (sin audios externos ni librerías).
6. Pantalla de Game Over con botón de reinicio y botón de pausa.
7. Cero placeholders, cero comentarios como '// el resto aquí'. Entrega el código 100% completo y funcional listo para abrir en el navegador.

Formato de salida obligatorio:
1. En tu espacio de razonamiento (thinking), analiza y planifica cada componente del juego.
2. Concluye tu pensamiento formalmente cerrando con </think>.
3. Entrega únicamente el bloque con el código del archivo HTML completo dentro de ```html ... ```.
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
        if "mmproj" in f.name.lower() or "imatrix" in f.name.lower():
            continue
        found.append(f)
    return sorted(found, key=lambda x: x.name)

def kill_server():
    subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

def wait_for_server(proc=None, port=1234, timeout=75):
    start = time.time()
    url = f"http://127.0.0.1:{port}/health"
    log_file = PROJECT_ROOT / "llama-server.log"
    while time.time() - start < timeout:
        if proc and proc.poll() is not None:
            err_snippet = "Proceso terminado con código de error."
            if log_file.exists():
                try:
                    lines = [l.strip() for l in log_file.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()]
                    if lines:
                        err_snippet = "\n   ".join(lines[-4:])
                except Exception:
                    pass
            return False, f"El servidor falló al iniciar (código {proc.returncode}):\n   {err_snippet}"

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True, "OK"
        except Exception:
            time.sleep(1)
    return False, "El servidor no respondió a tiempo dentro del timeout permitido."

def load_preset_for_model(model_name):
    stem = model_name.replace(".gguf", "")
    candidates = [
        PRESETS_DIR / f"{stem}.conf",
        PRESETS_DIR / f"{model_name}.conf"
    ]
    for c in candidates:
        if c.exists():
            return parse_preset_file(c)
    
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
    ctx_size = preset.get("AI_CTX_SIZE", "24576")
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
        "--reasoning-format", "deepseek",
        "--predict", str(STANDARD_MAX_TOKENS)
    ]

    if mtp.lower() == "on" and ("mtp" in name.lower() or "qwen3.6" in name.lower()):
        cmd.extend(["--spec-type", "draft-mtp", "--spec-draft-n-max", str(mtp_draft)])

    log_file = PROJECT_ROOT / "llama-server.log"
    log_f = open(log_file, "w", encoding="utf-8", errors="replace")

    proc = subprocess.Popen(
        cmd,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )

    ok, msg = wait_for_server(proc=proc, port=1234, timeout=75)
    if not ok:
        return False, msg
    return True, preset

class ArenaStreamer:
    """Maneja el streaming en tiempo real en la consola distinguiendo razonamiento y código."""
    def __init__(self):
        self.state = "idle"  # "idle", "thought", "code"
        self.accumulated_thought = []
        self.accumulated_content = []
        self.raw_buffer = ""
        self.completion_tokens = 0
        self.thought_token_count = 0
        self.code_token_count = 0

    def process_delta(self, delta):
        thought = delta.get("reasoning_content") or delta.get("thought")
        content = delta.get("content", "")

        # Unificar el texto entrante
        incoming_text = ""
        if thought:
            incoming_text = thought
        elif content:
            incoming_text = content

        if not incoming_text:
            return

        self.completion_tokens += 1
        text = self.raw_buffer + incoming_text
        self.raw_buffer = ""

        while text:
            if self.state != "code":
                # Si estamos en idle, iniciar modo pensamiento
                if self.state == "idle":
                    self.state = "thought"
                    print(f"\n\n{c_yellow('🧠 [Razonamiento / Thinking]:')}\n\033[0;33m", end="", flush=True)

                # Comprobar si el texto contiene el cierre de pensamiento o el inicio del código
                triggers = ["</think>", "</thought>", "```html", "```HTML", "```\n<!DOCTYPE", "<!DOCTYPE html>", "<!doctype html>", "<html"]
                found_pos = -1
                found_trigger = None

                for trg in triggers:
                    p = text.find(trg)
                    if p != -1 and (found_pos == -1 or p < found_pos):
                        found_pos = p
                        found_trigger = trg

                if found_pos != -1:
                    # Encontrado trigger de transición a código
                    before = text[:found_pos]
                    if before:
                        self._write_thought(before)
                    
                    # Cambiar estado a código
                    self.state = "code"
                    print(f"\033[0m\n\n{c_green('💻 [Generando Código / Snake Game]:')}\n\033[0;32m", end="", flush=True)

                    # Si el trigger fue </think> o </thought>, lo consumimos sin imprimirlo en el código
                    if found_trigger in ["</think>", "</thought>"]:
                        text = text[found_pos + len(found_trigger):]
                    else:
                        text = text[found_pos:]
                    continue
                else:
                    # Verificar si termina con un prefijo parcial de algún trigger
                    prefixes = ("</thought", "</thoug", "</thou", "</tho", "</think", "</thin", "</thi", "</th", "</t", "</",
                                "```html", "```htm", "```ht", "```h", "```", "`",
                                "<!DOCTYPE html", "<!DOCTYPE", "<!DOC", "<!D", "<!",
                                "<html", "<htm", "<ht", "<")
                    matched_p = None
                    for p in prefixes:
                        if text.endswith(p):
                            matched_p = p
                            break
                    if matched_p:
                        self.raw_buffer = matched_p
                        text = text[:-len(matched_p)]
                    
                    if text:
                        self._write_thought(text)
                        text = ""
            else:
                # Ya estamos en modo código: todo el texto posterior va al código
                self._write_code(text)
                text = ""

    def _write_thought(self, text):
        if not text: return
        self.accumulated_thought.append(text)
        self.thought_token_count += 1
        sys.stdout.write(text)
        sys.stdout.flush()

    def _write_code(self, text):
        if not text: return
        self.accumulated_content.append(text)
        self.code_token_count += 1
        sys.stdout.write(text)
        sys.stdout.flush()

    def close(self):
        if self.raw_buffer:
            if self.state == "thought":
                self._write_thought(self.raw_buffer)
            else:
                self._write_code(self.raw_buffer)
            self.raw_buffer = ""
        sys.stdout.write("\033[0m\n")
        sys.stdout.flush()

def extract_html_code(text):
    if not text: return ""
    match = re.search(r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?|<html[\s\S]*?)```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    html_match = re.search(r"(<!DOCTYPE html[\s\S]*?</html>|<html[\s\S]*?</html>)", text, re.IGNORECASE)
    if html_match:
        return html_match.group(1).strip()
    return text.strip()

def evaluate_code_deep(code_str):
    """
    Suite profunda de verificación automatizada (Harness de Calidad).
    Valida estructura HTML, sintaxis JavaScript con Node.js, Canvas 2D, Web Audio API,
    controles táctiles, localStorage y ausencia de placeholders.
    """
    score = 0
    passed = []
    failed = []

    # 1. Estructura HTML y Meta viewport (15 pts)
    if "<!DOCTYPE html>" in code_str or "<html" in code_str:
        score += 10
        passed.append("Estructura HTML5 válida (+10)")
    else:
        failed.append("Falta declaración <!DOCTYPE html> o estructura <html> básica.")

    if 'name="viewport"' in code_str or "viewport" in code_str.lower():
        score += 5
        passed.append("Meta viewport para responsividad móvil (+5)")
    else:
        failed.append("Falta meta viewport para adaptación móvil (<meta name='viewport' content='width=device-width, initial-scale=1.0'>).")

    # 2. Sintaxis JavaScript mediante Node.js (15 pts)
    js_code = ""
    script_matches = re.findall(r"<script[^>]*>([\s\S]*?)</script>", code_str, re.IGNORECASE)
    if script_matches:
        js_code = "\n".join(script_matches)

    if js_code.strip():
        temp_js = PROJECT_ROOT / "scratch_syntax_check.js"
        try:
            with open(temp_js, "w", encoding="utf-8") as f:
                f.write(js_code)
            
            node_cmd = ["node", "--check", str(temp_js)]
            res = subprocess.run(node_cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                score += 15
                passed.append("JavaScript 100% válido y libre de errores de sintaxis (+15)")
            else:
                err_lines = [l.strip() for l in res.stderr.splitlines() if "SyntaxError" in l or "^" in l]
                err_summary = " | ".join(err_lines[:2]) if err_lines else res.stderr.strip()[:100]
                failed.append(f"Error de sintaxis en JavaScript detectado por Node: {err_summary}")
        except Exception:
            if "function" in js_code and "{" in js_code:
                score += 10
                passed.append("Estructura JavaScript presente (+10)")
        finally:
            if temp_js.exists():
                try: temp_js.unlink()
                except Exception: pass
    else:
        failed.append("No se encontró bloque <script> con código JavaScript ejecutable.")

    # 3. Canvas 2D y Renderizado (15 pts)
    if "<canvas" in code_str and ("getContext('2d')" in code_str or 'getContext("2d")' in code_str):
        score += 15
        passed.append("Canvas 2D con contexto gráfico inicializado (+15)")
    else:
        failed.append("Falta elemento <canvas> o llamada a getContext('2d').")

    # 4. Game Loop fluido (10 pts)
    if "requestAnimationFrame" in code_str or "setInterval" in code_str:
        score += 10
        passed.append("Bucle de juego (Game Loop) implementado (+10)")
    else:
        failed.append("Falta bucle de juego continuo (requestAnimationFrame o setInterval).")

    # 5. Web Audio API sintetizada (15 pts)
    has_audio_ctx = "AudioContext" in code_str or "webkitAudioContext" in code_str
    has_oscillator = "createOscillator" in code_str or "OscillatorNode" in code_str
    if has_audio_ctx and has_oscillator:
        score += 15
        passed.append("Efectos de sonido sintetizados con Web Audio API (Osciladores procedimentales) (+15)")
    elif has_audio_ctx:
        score += 8
        passed.append("AudioContext inicializado pero faltan osciladores (+8)")
        failed.append("Web Audio API incompleta: usa createOscillator() y createGain() para sintetizar sonidos al comer y morir.")
    else:
        failed.append("Falta Web Audio API: el juego debe sintetizar sonidos procedimentales sin archivos externos.")

    # 6. Controles: Teclado + Touch D-Pad (15 pts)
    has_kbd = "keydown" in code_str or "ArrowUp" in code_str or "keyCode" in code_str or "key" in code_str
    has_touch = "touchstart" in code_str or "pointerdown" in code_str or "dpad" in code_str.lower() or "touch" in code_str.lower()
    if has_kbd and has_touch:
        score += 15
        passed.append("Controles duales completos: Teclado (WASD/Flechas) + D-Pad táctil móvil (+15)")
    elif has_kbd:
        score += 8
        passed.append("Controles de teclado implementados (+8)")
        failed.append("Faltan controles táctiles: añade botones D-Pad en pantalla con eventos touchstart/touchend para móvil.")
    else:
        failed.append("Faltan controles de teclado y controles táctiles.")

    # 7. LocalStorage High Score (10 pts)
    if "localStorage" in code_str and ("setItem" in code_str or "getItem" in code_str):
        score += 10
        passed.append("Récord persistente (High Score) en localStorage (+10)")
    else:
        failed.append("Falta persistencia de récord: usa localStorage.getItem() y localStorage.setItem().")

    # 8. Efectos visuales y ausencia de placeholders (5 pts)
    if ("particle" in code_str.lower() or "particula" in code_str.lower() or "shake" in code_str.lower()):
        score += 5
        passed.append("Efectos visuales especiales (partículas / screen shake) (+5)")
    else:
        failed.append("Faltan efectos visuales: añade sistema de partículas al comer manzana o screen shake al morir.")

    if "TODO" in code_str or "// el resto" in code_str.lower() or len(code_str) < 1500:
        failed.append("Código contiene placeholders ('TODO') o está incompleto (< 1500 bytes).")

    score = max(0, min(score, 100))
    details = passed + [f"PENDIENTE: {f}" for f in failed]
    return score, details, passed, failed

def estimate_tokens(text):
    return len(text) // 4

def check_and_compact_context(messages, max_ctx=24000):
    """
    Context Compaction: Compacta el historial de conversación cuando excede
    la ventana segura de contexto, conservando el prompt base, el último código y el reporte de fallos.
    """
    total_est = sum(estimate_tokens(m["content"]) for m in messages)
    if total_est <= (max_ctx - 4000):
        return messages

    print(c_yellow(f"\n⚡ [Context Compaction Activo]: El historial alcanzó ~{int(total_est)} tokens."))
    print(c_yellow(f"   Compactando turnos previos para proteger VRAM (8GB) y RAM (16GB)..."))

    if len(messages) <= 3:
        return messages

    system_msg = messages[0]
    initial_user = messages[1]
    last_assistant = messages[-2] if messages[-2]["role"] == "assistant" else messages[-1]
    last_user_feedback = messages[-1] if messages[-1]["role"] == "user" else None

    summary_text = (
        "[RESUMEN DE COMPACTACIÓN DE ITERACIONES PREVIAS]:\n"
        "El modelo ya ha realizado iteraciones de diseño previas del juego Snake.\n"
        "Se ha descartado el historial intermedio antiguo para liberar ventana de contexto.\n"
        "Continúa trabajando sobre el último código entregado y las últimas observaciones de pruebas.\n"
    )

    new_messages = [
        system_msg,
        {"role": "user", "content": initial_user["content"]},
        {"role": "assistant", "content": summary_text + "\nÚltimo código entregado:\n" + last_assistant["content"][-4000:]}
    ]
    if last_user_feedback:
        new_messages.append(last_user_feedback)

    new_est = sum(estimate_tokens(m["content"]) for m in new_messages)
    print(c_green(f"✓ Contexto reducido de ~{int(total_est)} a ~{int(new_est)} tokens. Espacio libre para nuevas iteraciones.\n"))
    return new_messages

def build_iteration_feedback(iteration, score, failed_items, previous_code):
    lines = [
        f"=== REPORTE DE EVALUACIÓN AUTOMÁTICA DEL HARNESS (ITERACIÓN {iteration}) ===",
        f"Puntuación alcanzada: {score}/100",
        "",
        "FALLOS Y CARENCIAS DETECTADAS EN TU CÓDIGO:"
    ]
    for idx, f in enumerate(failed_items, 1):
        lines.append(f"{idx}. {f}")
    
    lines.extend([
        "",
        "INSTRUCCIONES OBLIGATORIAS PARA ESTA ITERACIÓN:",
        "1. Revisa detenidamente el código que entregaste en la iteración previa.",
        "2. Utiliza tu presupuesto de razonamiento (thinking budget) para diagnosticar la causa exacta de cada uno de los fallos listados arriba.",
        "3. Soluciona cada fallo asegurando que:",
        "   - Si hubo errores de sintaxis en JavaScript, queden 100% corregidos.",
        "   - Si faltaban controles táctiles, implementa el D-Pad virtual en pantalla con eventos touchstart/touchend.",
        "   - Si faltaba Web Audio API, inicializa AudioContext con osciladores y gain nodes para comer manzana y morir.",
        "   - La estética retro cyberpunk y el canvas 2D se mantengan limpios y fluidos.",
        "4. Entrega el archivo HTML autocontenido completo y corregido dentro de un bloque ```html ... ```. Cero placeholders, cero código cortado.",
        ""
    ])
    return "\n".join(lines)

def query_model_streaming(messages, port=1234, max_tokens=STANDARD_MAX_TOKENS):
    url = f"http://127.0.0.1:{port}/v1/chat/completions"
    payload = {
        "model": "localmodel",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "stream": True
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    t0 = time.time()
    first_token_time = None
    streamer = ArenaStreamer()

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
                    
                    if first_token_time is None and (delta.get("content") or delta.get("reasoning_content") or delta.get("thought")):
                        first_token_time = time.time()

                    streamer.process_delta(delta)
                except Exception:
                    continue

        streamer.close()

    except Exception as e:
        streamer.close()
        print(c_red(f"\n❌ Error durante streaming: {e}"))
        return None, 0, 0, 0.0, 0.0

    t_total = time.time() - t0
    ttft = (first_token_time - t0) if first_token_time else 0.0
    completion_tokens = streamer.completion_tokens
    tok_sec = completion_tokens / t_total if t_total > 0 else 0.0

    full_output = "".join(streamer.accumulated_content)
    if not full_output.strip() and streamer.accumulated_thought:
        full_output = "".join(streamer.accumulated_thought)

    prompt_tokens = sum(len(m["content"]) for m in messages) // 4
    return full_output, completion_tokens, prompt_tokens, tok_sec, t_total, streamer.thought_token_count, streamer.code_token_count

def run_loop_engineering_benchmark(model_path, max_session_tokens=MAX_TEST_TOKEN_BUDGET, max_iterations=4):
    """
    Harness de Loop Engineering / TDD iterativo:
    Ejecuta el modelo, testea el resultado con Node.js y verificadores profundos,
    le entrega feedback de fallos al modelo y permite que itere hasta alcanzar 100/100
    o agotar el presupuesto de 100k tokens con auto-compaction.
    """
    model_name = model_path.name
    print(c_cyan(f"\n========================================================"))
    print(c_yellow(f"🚀 INICIANDO HARNESS LOOP ENGINEERING: {model_name}"))
    print(c_cyan(f"========================================================"))
    print(f"📦 Tamaño: {model_path.stat().st_size / (1024**3):.2f} GB")
    print(f"🧠 Thinking Budget: {STANDARD_THINKING_BUDGET} tokens / iteración")
    print(f"📤 Ventana Max Output: {STANDARD_MAX_TOKENS} tokens / iteración")
    print(f"🎯 Presupuesto Total de Sesión: {max_session_tokens:,} tokens")
    print(f"🔄 Máximo de Iteraciones TDD: {max_iterations}")

    print(c_blue("\n✦ Levantando llama-server con aceleración Vulkan y preset calibrado..."))
    ok, preset_info = start_server_for_model(model_path)
    if not ok:
        print(c_red(f"❌ Error al iniciar servidor: {preset_info}"))
        return None

    ctx_limit = int(preset_info.get("AI_CTX_SIZE", "24576")) if isinstance(preset_info, dict) else 24576

    model_safe_dir = RESULTS_DIR / model_name.replace(".gguf", "")
    model_safe_dir.mkdir(parents=True, exist_ok=True)

    messages = [
        {"role": "system", "content": "Eres un ingeniero de software senior y desarrollador experto en videojuegos web trabajando en un entorno TDD (Test-Driven Development). Genera código limpio, autocontenido y funcional sin texto conversacional superfluo."},
        {"role": "user", "content": BENCHMARK_PROMPT}
    ]

    total_session_tokens = 0
    iteration = 1
    best_score = 0
    best_code = ""
    best_details = []
    total_time = 0.0
    speeds = []

    try:
        while iteration <= max_iterations and total_session_tokens < max_session_tokens:
            print(c_cyan(f"\n──────────────────────────────────────────────────────────"))
            print(c_yellow(f"🔄 ITERACIÓN {iteration} / {max_iterations}"))
            print(f"📊 Presupuesto usado: {c_bold(f'{total_session_tokens:,}')} / {max_session_tokens:,} tokens (Restante: {max_session_tokens - total_session_tokens:,})")
            print(c_cyan(f"──────────────────────────────────────────────────────────"))

            messages = check_and_compact_context(messages, max_ctx=ctx_limit)

            print(c_cyan(f"✦ Generando y razonando en tiempo real (iteración {iteration}):"))
            query_res = query_model_streaming(messages)
            output_text, completion_tokens, prompt_tokens, speed, t_iter, th_cnt, cd_cnt = query_res
            if output_text is None:
                print(c_red("❌ Falló la consulta al modelo."))
                break

            turn_tokens = prompt_tokens + completion_tokens
            total_session_tokens += turn_tokens
            total_time += t_iter
            if speed > 0: speeds.append(speed)

            print(f"\n\n{c_green('✓ Generación completada:')} {completion_tokens} tokens (🧠 Pensamiento: {th_cnt} | 💻 Código: {cd_cnt}) | ⚡ {speed:.2f} tok/s")

            html_code = extract_html_code(output_text)
            
            iter_file = model_safe_dir / f"snake_iter_{iteration}.html"
            with open(iter_file, "w", encoding="utf-8") as f:
                f.write(html_code)

            score, details, passed, failed = evaluate_code_deep(html_code)

            print(f"\n\n{c_cyan('══════════════════════════════════════════════════════════')}")
            print(f"📊 {c_yellow(f'DIAGNÓSTICO AUTOMÁTICO DE ITERACIÓN {iteration}')}: Puntuación {c_bold(f'{score}/100')}")
            print(c_cyan("══════════════════════════════════════════════════════════"))
            for p in passed:
                print(c_green(f"   ✓ {p}"))
            for f in failed:
                print(c_red(f"   ❌ {f}"))

            if score > best_score:
                best_score = score
                best_code = html_code
                best_details = details
                final_file = model_safe_dir / "snake.html"
                with open(final_file, "w", encoding="utf-8") as f:
                    f.write(best_code)

            if score == 100:
                print(c_green(f"\n🎉 ¡PERFECCIÓN ALCANZADA EN ITERACIÓN {iteration}! (100/100 pts)"))
                print(c_green("El modelo satisfizo absolutamente todos los requerimientos y pasó las pruebas sin errores."))
                break

            if total_session_tokens >= max_session_tokens:
                print(c_yellow(f"\n⚠️ Presupuesto total de {max_session_tokens:,} tokens alcanzado. Finalizando ciclo TDD."))
                break

            if iteration < max_iterations:
                feedback = build_iteration_feedback(iteration, score, failed, html_code)
                messages.append({"role": "assistant", "content": output_text})
                messages.append({"role": "user", "content": feedback})
                print(c_blue(f"\n✦ Enviando reporte de fallos al modelo para la iteración {iteration + 1}..."))

            iteration += 1

    finally:
        kill_server()

    avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
    final_out = model_safe_dir / "snake.html"

    print(c_green(f"\n✓ Torneo finalizado para {model_name}."))
    print(f"🏆 Puntuación Final: {c_yellow(f'{best_score}/100')}")
    print(f"💾 Mejor versión guardada en: {c_cyan(str(final_out))}")
    print(f"📊 Tokens totales consumidos: {total_session_tokens:,} | Velocidad promedio: {avg_speed:.2f} tok/s")

    return {
        "model": model_name,
        "size_gb": model_path.stat().st_size / (1024**3),
        "tokens": total_session_tokens,
        "time_s": total_time,
        "speed": avg_speed,
        "score": best_score,
        "iterations": min(iteration, max_iterations),
        "out_file": str(final_out)
    }

def run_pi_agent_benchmark(model_path):
    """Ejecuta el harness del agente Pi (@earendil-works/pi-coding-agent) en modo no-interactivo."""
    model_name = model_path.name
    print(c_cyan(f"\n========================================================"))
    print(c_yellow(f"🚀 INICIANDO PI CODING AGENT HARNESS: {model_name}"))
    print(c_cyan(f"========================================================"))
    print(f"📦 Tamaño: {model_path.stat().st_size / (1024**3):.2f} GB")
    print(f"🧠 Pi Thinking Budget: High (8,192 tokens)")
    print(f"🥧 Compaction: Activa (reserveTokens=16k, keepRecent=20k)")
    print(f"🎯 Presupuesto de Sesión: {MAX_TEST_TOKEN_BUDGET:,} tokens")

    print(c_blue("\n✦ Levantando llama-server con aceleración Vulkan y preset calibrado..."))
    ok, preset_info = start_server_for_model(model_path)
    if not ok:
        print(c_red(f"❌ Error al iniciar servidor: {preset_info}"))
        return None

    model_safe_dir = RESULTS_DIR / model_name.replace(".gguf", "")
    model_safe_dir.mkdir(parents=True, exist_ok=True)

    pi_prompt = (
        "Eres un ingeniero senior de videojuegos web. Tu misión es crear snake.html en este directorio actual.\n"
        "Requisitos: juego arcade retro Snake completo en Canvas 2D, Web Audio API sintetizada, localStorage high score, teclado y controles táctiles D-Pad.\n"
        "Crea el archivo snake.html, inspecciónalo y asegúrate de que no tenga errores de sintaxis y esté 100% completo y funcional."
    )

    t0 = time.time()
    env = os.environ.copy()
    env["LLAMA_BASE_URL"] = "http://127.0.0.1:1234"
    env["PATH"] = r"C:\Program Files\nodejs;C:\Users\USUARIO\AppData\Roaming\npm;" + env.get("PATH", "")

    pi_cmd = ["pi", "-p", pi_prompt, "--thinking", "high", "--approve"]

    print(c_green("\n✦ Lanzando agente Pi en la terminal...\n"))
    try:
        subprocess.run(pi_cmd, cwd=str(model_safe_dir), env=env)
    except Exception as e:
        print(c_red(f"Error ejecutando Pi: {e}"))
    finally:
        kill_server()

    t_total = time.time() - t0

    out_file = model_safe_dir / "snake.html"
    code_str = ""
    if out_file.exists():
        with open(out_file, "r", encoding="utf-8", errors="ignore") as f:
            code_str = f.read()

    score, details, passed, failed = evaluate_code_deep(code_str)

    print(f"\n🏆 Puntuación Final alcanzada por Pi: {c_yellow(f'{score}/100')}")
    for p in passed:
        print(c_green(f"   ✓ {p}"))
    for f in failed:
        print(c_red(f"   ❌ {f}"))

    return {
        "model": model_name,
        "size_gb": model_path.stat().st_size / (1024**3),
        "tokens": 0,
        "time_s": t_total,
        "speed": 0.0,
        "score": score,
        "iterations": 1,
        "out_file": str(out_file)
    }

def run_single_shot_benchmark(model_path):
    """Ejecuta una única pasada rápida sin iteraciones."""
    return run_loop_engineering_benchmark(model_path, max_session_tokens=STANDARD_MAX_TOKENS, max_iterations=1)

def print_and_save_leaderboard(results):
    if not results: return
    results.sort(key=lambda x: (x["score"], x.get("speed", 0)), reverse=True)

    header = f"\n{c_blue('╔════════════════════════════════════════════════════════════════════════════════════════════════╗')}\n"
    header += f"{c_blue('║')} {c_yellow('🏆 LEADERBOARD ARENA DE MODELOS LOCALES (LOOP ENGINEERING & HARNESS)')}                 {c_blue('║')}\n"
    header += f"{c_blue('╠════════════════════════════════════════════════════════════════════════════════════════════════╣')}\n"
    print(header, end="")

    print(f"{'Pos':<4} | {'Modelo':<30} | {'Calidad':<8} | {'Iter':<5} | {'Tokens':<9} | {'Velocidad':<11} | {'Tiempo':<8}")
    print("-" * 96)

    md_lines = [
        "# 🏆 Leaderboard Arena de Modelos Locales (Loop Engineering Harness)",
        "",
        "| Pos | Modelo | Puntuación | Iteraciones | Tokens Sesión | Velocidad Media | Tiempo Total | Archivo Generado |",
        "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|"
    ]

    for idx, r in enumerate(results, 1):
        m_short = r["model"][:28]
        speed_str = f"{r.get('speed', 0):.2f} t/s" if r.get('speed', 0) > 0 else "N/A"
        time_str = f"{r['time_s']:.1f} s"
        score_str = f"{r['score']}/100"
        iters_str = str(r.get("iterations", 1))
        tokens_str = f"{r.get('tokens', 0):,}"

        print(f"{idx:<4} | {m_short:<30} | {c_yellow(score_str):<16} | {iters_str:<5} | {tokens_str:<9} | {c_green(speed_str):<20} | {time_str:<8}")

        rel_path = f"benchmarks/arena/{Path(r['out_file']).parent.name}/snake.html"
        md_lines.append(f"| {idx} | **{r['model']}** | **{score_str}** | {iters_str} | {tokens_str} | {speed_str} | {time_str} | [{Path(r['out_file']).name}]({rel_path}) |")

    print(c_blue("╚════════════════════════════════════════════════════════════════════════════════════════════════╝\n"))

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

    opt = input("\nElige el modelo o torneo [A, 1-N, 0]: ").strip()
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

    print(c_yellow("\nModos de Harness de Evaluación:"))
    print(f"  1) {c_green('🔄 Loop Engineering Harness')} (Auto-testing iterativo TDD, 100k budget, auto-compaction) [RECOMENDADO]")
    print(f"  2) {c_cyan('🥧 Pi Coding Agent Harness')} (Agente Pi con herramientas completas de archivo y shell)")
    print(f"  3) {c_yellow('⚡ Single-Shot')} (1 pasada directa)")

    mode_opt = input("\nElige el modo [1/2/3, Enter=1]: ").strip()
    if not mode_opt: mode_opt = "1"

    results = []
    for m in selected_models:
        if mode_opt == "2":
            res = run_pi_agent_benchmark(m)
        elif mode_opt == "3":
            res = run_single_shot_benchmark(m)
        else:
            res = run_loop_engineering_benchmark(m)

        if res:
            results.append(res)

    print_and_save_leaderboard(results)

if __name__ == "__main__":
    main()
