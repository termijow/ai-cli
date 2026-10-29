#!/usr/bin/env python3
"""
ai-models.py - AI-CLI Native Model Selector
Works 100% natively on Windows, macOS, and Linux without bash dependencies.
Features:
- Zero-friction instant model selection (auto-applies presets with 1 keypress)
- Intelligent MTP / DFlash auto-association (Nemotron <-> dflash, Gemma <-> mtp)
- Advanced tuning mode (--tune or -t) for custom context, layers, and thinking
- CLI non-interactive support (--list, --select <name_or_number>)
"""

import os
import sys
import glob
import argparse
from pathlib import Path

# Configurar salida UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
BOLD = "\033[1m"
NC = "\033[0m"


def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def save_env_key(path: Path, updates: dict):
    lines = []
    keys_updated = set()
    if path.exists():
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    k, _ = stripped.split("=", 1)
                    k = k.strip()
                    if k in updates:
                        lines.append(f"{k}={updates[k]}\n")
                        keys_updated.add(k)
                        continue
                lines.append(line)
    for k, v in updates.items():
        if k not in keys_updated:
            lines.append(f"{k}={v}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_model_recommendations(model_name: str, size_bytes: int):
    size_mb = size_bytes / (1024 * 1024)
    size_gb = size_mb / 1024

    if "35B-A3B" in model_name.upper() or "A3B" in model_name.upper():
        if "IQ2" in model_name.upper():
            return f"{size_gb:.2f}", 28, "🟡 MoE Híbrido GPU+RAM (~6.8GB VRAM + ~3.4GB RAM)", "moe_a3b"
        else:
            return f"{size_gb:.2f}", 21, "🟡 MoE Híbrido GPU+RAM (~6.6GB VRAM + ~6.5GB RAM)", "moe_a3b"

    if size_mb <= 3500:
        return f"{size_gb:.2f}", 99, "🟢 100% en GPU VRAM (Ultra Rápido)", "small"
    elif size_mb <= 7300:
        return f"{size_gb:.2f}", 99, "🟢 100% en GPU VRAM (Rápido)", "small"
    elif size_mb <= 11000:
        return f"{size_gb:.2f}", 40, "🟡 GPU Offload Híbrido (~7GB VRAM + ~1.5GB RAM)", "medium"
    elif size_mb <= 16000:
        return f"{size_gb:.2f}", 25, "🟠 GPU Offload Híbrido (~4.5GB VRAM + ~8GB RAM)", "large"
    else:
        return f"{size_gb:.2f}", 15, "🔴 Principalmente en RAM (~3.5GB VRAM + RAM alta)", "large"


def find_all_models(include_auxiliary: bool = False):
    search_dirs = [
        PROJECT_ROOT / "models",
        Path.home() / "models",
        Path(f"C:/Users/{os.environ.get('USERNAME', 'USUARIO')}/models"),
    ]
    seen = {}
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*.gguf"):
            if p.is_file():
                p_lower = p.name.lower()
                is_aux = p_lower.startswith("mtp-") or p_lower.startswith("dflash-") or "mmproj" in p_lower or "imatrix" in p_lower
                if not include_auxiliary and is_aux:
                    continue
                if p.name not in seen:
                    try:
                        seen[p.name] = (p, p.stat().st_size)
                    except Exception:
                        seen[p.name] = (p, 0)
    return seen


def find_preset(model_name: str) -> dict:
    stem = model_name[:-5] if model_name.endswith(".gguf") else model_name
    presets_dir = PROJECT_ROOT / "presets"
    if not presets_dir.exists():
        return {}
    preset_file = presets_dir / f"{stem}.conf"
    if not preset_file.exists():
        preset_file = presets_dir / f"{model_name}.conf"
    if not preset_file.exists():
        # Búsqueda por coincidencia
        stem_l = stem.lower()
        candidates = list(presets_dir.glob("*.conf"))
        for f in candidates:
            f_stem_l = f.stem.lower()
            if stem_l == f_stem_l:
                preset_file = f
                break
        if not preset_file.exists():
            for f in candidates:
                f_stem_l = f.stem.lower()
                if "nemotron" in stem_l and "nemotron" in f_stem_l and ("q6" in stem_l and "q6" in f_stem_l or "q4" in stem_l and "q4" in f_stem_l):
                    preset_file = f
                    break
                elif "gemma-4-e4b" in stem_l and "gemma-4-e4b" in f_stem_l and ("q8" in stem_l and "q8" in f_stem_l or "q6" in stem_l and "q6" in f_stem_l or "turbo" in f_stem_l):
                    preset_file = f
                    break
                elif "gemma-4-e2b" in stem_l and "gemma-4-e2b" in f_stem_l:
                    preset_file = f
                    break
                elif stem_l in f_stem_l or f_stem_l in stem_l:
                    preset_file = f
                    break
    if preset_file.exists():
        return load_env(preset_file)
    return {}


def resolve_auto_draft(model_name: str, all_drafts: dict) -> tuple:
    """
    Auto-asocia inteligentemente un modelo base con su modelo draft MTP o especulativo.
    Retorna: (spec_type, draft_model_name, draft_tokens)
    """
    m_lower = model_name.lower()

    # 1. NVIDIA Nemotron 3.5 Bolt -> DFlash Q8_0
    if "nemotron" in m_lower or "bolt" in m_lower:
        for d in all_drafts:
            d_l = d.lower()
            if "dflash" in d_l and ("nemotron" in d_l or "bolt" in d_l or "e4b" in d_l):
                return "draft-mtp", d, "3"
        return "draft-mtp", "dflash-NVIDIA-Nemotron-3.5-Bolt-E4B-Q8_0.gguf", "3"

    # 2. Gemma 4 E4B -> mtp-gemma-4-E4B-it
    if "gemma-4-e4b" in m_lower or "gemma-4-4b" in m_lower or "gemma-e4b" in m_lower:
        for d in all_drafts:
            d_l = d.lower()
            if "mtp" in d_l and "e4b" in d_l:
                return "draft-mtp", d, "3"
        return "draft-mtp", "mtp-gemma-4-E4B-it-Q4_0.gguf", "3"

    # 3. Gemma 4 E2B -> mtp-gemma-4-E2B-it
    if "gemma-4-e2b" in m_lower or "gemma-4-2b" in m_lower or "gemma-e2b" in m_lower:
        for d in all_drafts:
            d_l = d.lower()
            if "mtp" in d_l and "e2b" in d_l:
                return "draft-mtp", d, "3"
        return "draft-mtp", "mtp-gemma-4-E2B-it-Q4_0.gguf", "3"

    # 4. Qwen 3.5 9B -> Qwen 3.5 0.8B (Draft Model auxiliar)
    if ("qwen3.5-9b" in m_lower or "qwen-3.5-9b" in m_lower) and not "0.8b" in m_lower:
        for d in all_drafts:
            d_l = d.lower()
            if "0.8b" in d_l and not "mmproj" in d_l:
                return "draft-simple", d, "3"
        return "draft-simple", "Qwen3.5-0.8B-UD-Q8_K_XL.gguf", "3"

    return "none", "", "3"


def main():
    arg_parser = argparse.ArgumentParser(description="AI-CLI Native Model Selector")
    arg_parser.add_argument("--tune", "-t", action="store_true", help="Abrir modo de ajuste manual de capas y contexto")
    arg_parser.add_argument("--list", "-l", action="store_true", help="Listar modelos disponibles en formato plano")
    arg_parser.add_argument("--select", "-s", type=str, default=None, help="Seleccionar modelo por número o nombre")
    args = arg_parser.parse_args()

    env = load_env(ENV_FILE)
    current_model = env.get("MODEL_FILE", "")
    current_layers = env.get("AI_GPU_LAYERS", "99")
    current_ctx = env.get("AI_CTX_SIZE", "16384")
    current_thinking = env.get("AI_THINKING_LEVEL", "high")
    current_reasoning = env.get("AI_REASONING", "on")
    current_max_tokens = env.get("AI_MAX_TOKENS", "16384")

    models = find_all_models()
    all_drafts = find_all_models(include_auxiliary=True)

    if not models:
        print(f"{RED}❌ No se encontraron modelos .gguf en models/ ni en ~/models{NC}")
        print(f"{YELLOW}💡 Puedes colocar tus modelos .gguf en: {PROJECT_ROOT / 'models'}{NC}")
        sys.exit(1)

    model_names = sorted(models.keys())

    if args.list:
        for idx, name in enumerate(model_names, 1):
            path, sz = models[name]
            size_gb_str, _, _, _ = get_model_recommendations(name, sz)
            active = " [ACTIVO]" if name == current_model else ""
            print(f"{idx}: {name} ({size_gb_str} GB){active}")
        sys.exit(0)

    # Menú Principal
    print(f"\n{BLUE}╭──────────────────────────────────────────────────────────────╮{NC}")
    print(f"{BLUE}│{NC} {YELLOW}🤖 SELECTOR INTELIGENTE DE MODELOS LOCALES AI-CLI{NC}            {BLUE}│{NC}")
    print(f"{BLUE}├──────────────────────────────────────────────────────────────┤{NC}")

    for idx, name in enumerate(model_names, 1):
        path, sz = models[name]
        size_gb_str, rec_l, status, _ = get_model_recommendations(name, sz)
        active_tag = f" {GREEN}[ACTIVO]{NC}" if name == current_model else ""
        
        # Detectar auto-asociación MTP
        preset = find_preset(name)
        preset_draft = preset.get("AI_MODEL_DRAFT", "")
        auto_spec, auto_draft, _ = resolve_auto_draft(name, all_drafts)
        draft_tag = ""
        if preset_draft or auto_draft:
            effective_draft = preset_draft or auto_draft
            short_draft = effective_draft.replace(".gguf", "")
            if "dflash" in short_draft.lower():
                draft_tag = f" {CYAN}⚡ [DFlash MTP Auto]{NC}"
            elif "mtp" in short_draft.lower():
                draft_tag = f" {CYAN}⚡ [MTP Auto]{NC}"
            else:
                draft_tag = f" {MAGENTA}⚡ [Draft Auto]{NC}"

        name_display = name[:38]
        print(f"{BLUE}│{NC} {BOLD}{idx:2d}){NC} {name_display:<38} {size_gb_str:>5} GB{active_tag}{draft_tag}")
        print(f"{BLUE}│{NC}     ↳ {status}")

    print(f"{BLUE}╰──────────────────────────────────────────────────────────────╯{NC}")
    print(f"{YELLOW}💡 Tip:{NC} Escribe el número para selección instantánea (ej: {BOLD}1{NC}).")
    print(f"       Para ajuste manual de capas/contexto escribe: {BOLD}1 -t{NC}\n")

    tune_mode = args.tune
    choice = args.select

    if not choice:
        try:
            choice = input(f"Elige número de modelo [1-{len(model_names)}] (o 'q' para salir): ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{YELLOW}Selección cancelada.{NC}")
            sys.exit(0)

    if not choice or choice.lower() in ["q", "exit", "quit"]:
        print(f"{YELLOW}Selección cancelada.{NC}")
        sys.exit(0)

    # Interpretar si el usuario agregó '-t' o 'tune'
    choice_parts = choice.split()
    target_num = choice_parts[0]
    if len(choice_parts) > 1 and choice_parts[1].lower() in ["-t", "--tune", "t", "tune", "custom"]:
        tune_mode = True

    try:
        choice_idx = int(target_num) - 1
        if not (0 <= choice_idx < len(model_names)):
            raise ValueError()
    except ValueError:
        # Búsqueda por substring de nombre
        matched = [i for i, n in enumerate(model_names) if target_num.lower() in n.lower()]
        if len(matched) == 1:
            choice_idx = matched[0]
        else:
            print(f"{RED}❌ Opción o modelo no encontrado.{NC}")
            sys.exit(1)

    selected_model = model_names[choice_idx]
    _, sz_bytes = models[selected_model]
    size_gb_str, rec_layers, status, tier = get_model_recommendations(selected_model, sz_bytes)
    preset = find_preset(selected_model)

    # Preset / Defaults óptimos
    preset_layers = preset.get("AI_GPU_LAYERS", str(rec_layers))
    suggested_ctx = preset.get("AI_CTX_SIZE", "24576" if tier == "small" else "16384")
    suggested_thinking = preset.get("AI_THINKING_LEVEL", "high")
    suggested_reasoning = preset.get("AI_REASONING", "on")
    suggested_max = preset.get("AI_MAX_TOKENS", "16384")
    preset_spec_type = preset.get("AI_SPEC_TYPE")
    preset_model_draft = preset.get("AI_MODEL_DRAFT")
    preset_draft_n_max = preset.get("AI_SPEC_DRAFT_N_MAX", "3")
    preset_fit = preset.get("AI_FIT", "on")
    preset_top_p = preset.get("AI_TOP_P", "0.95")
    preset_top_k = preset.get("AI_TOP_K", "40")
    preset_temp = preset.get("AI_TEMPERATURE", "0.6")

    # Auto-asociación MTP / Draft
    auto_spec, auto_draft, auto_draft_n = resolve_auto_draft(selected_model, all_drafts)
    final_spec_type = preset_spec_type or auto_spec
    final_model_draft = preset_model_draft or auto_draft
    final_draft_n = preset_draft_n_max or auto_draft_n

    # ==============================================================================
    # MODO INSTANTÁNEO (CERO FRICCIÓN - AUTO-ASOCIACIÓN SIN CONFIRMACIÓN REPETITIVA)
    # ==============================================================================
    if not tune_mode:
        mtp_display = f"{final_model_draft} ({final_spec_type}, {final_draft_n} tokens)" if final_model_draft else "Desactivado"
        
        print(f"\n{GREEN}╭──────────────────────────────────────────────────────────────╮{NC}")
        print(f"{GREEN}│{NC} {BOLD}⚡ MODELO Y ACELERACIÓN CONFIGURADOS AL INSTANTE{NC}              {GREEN}│{NC}")
        print(f"{GREEN}├──────────────────────────────────────────────────────────────┤{NC}")
        print(f"{GREEN}│{NC} 📦 {BOLD}Modelo:{NC}       {selected_model}")
        print(f"{GREEN}│{NC} ⚖️ {BOLD}Tamaño:{NC}       {size_gb_str} GB | {status}")
        print(f"{GREEN}│{NC} 🚀 {BOLD}MTP / Draft:{NC}  {CYAN}{mtp_display}{NC}")
        print(f"{GREEN}│{NC} 🎯 {BOLD}Capas GPU:{NC}    {preset_layers} capas")
        print(f"{GREEN}│{NC} 📏 {BOLD}Contexto:{NC}     {suggested_ctx} tokens")
        print(f"{GREEN}│{NC} 🧠 {BOLD}Thinking:{NC}     {suggested_thinking} (Reasoning: {suggested_reasoning})")
        print(f"{GREEN}│{NC} ⚖️ {BOLD}Fit VRAM:{NC}     {preset_fit}")
        print(f"{GREEN}╰──────────────────────────────────────────────────────────────╯{NC}")

        updates = {
            "MODEL_FILE": selected_model,
            "MODEL_REPO": preset.get("MODEL_REPO", f"local/{selected_model}"),
            "AI_GPU_LAYERS": preset_layers,
            "AI_CTX_SIZE": suggested_ctx,
            "AI_REASONING": suggested_reasoning,
            "AI_THINKING_LEVEL": suggested_thinking,
            "AI_MAX_TOKENS": suggested_max,
            "AI_SPEC_TYPE": final_spec_type,
            "AI_MODEL_DRAFT": final_model_draft,
            "AI_SPEC_DRAFT_N_MAX": final_draft_n,
            "AI_FIT": preset_fit,
        }
        if preset_top_p: updates["AI_TOP_P"] = preset_top_p
        if preset_top_k: updates["AI_TOP_K"] = preset_top_k
        if preset_temp: updates["AI_TEMPERATURE"] = preset_temp

        save_env_key(ENV_FILE, updates)
        print(f"{GREEN}✅ Guardado correctamente en .env{NC}")

        # Preguntar sólo si desea iniciar/reiniciar
        try:
            restart = input(f"\n{YELLOW}¿Deseas iniciar o reiniciar 'ai-serve' ahora con este modelo? (s/n) [s]: {NC}").strip()
        except (EOFError, KeyboardInterrupt):
            restart = "n"

        if restart.lower() in ["s", "y", ""]:
            print(f"\n✦ Deteniendo servidor anterior...")
            if sys.platform == "win32":
                os.system('taskkill /F /IM llama-server.exe >nul 2>&1')
            else:
                os.system('pkill -f llama-server >/dev/null 2>&1')
            print(f"✦ Iniciando ai-serve...")
            serve_bat = PROJECT_ROOT / "bin" / "ai-serve.bat"
            if sys.platform == "win32" and serve_bat.exists():
                os.system(f'"{serve_bat}"')
            else:
                os.system(f'"{PROJECT_ROOT / "bin" / "ai-serve"}"')
        else:
            print(f"✦ Puedes iniciar el servidor cuando quieras con: {BOLD}ai serve{NC}\n")
        return

    # ==============================================================================
    # MODO TUNING / AJUSTE MANUAL AVANZADO (--tune / -t)
    # ==============================================================================
    print(f"\n{GREEN}✔ Modo Tuning Activo para:{NC} {BOLD}{selected_model}{NC} ({size_gb_str} GB)")
    print(f"✦ Recomendación: {BOLD}{preset_layers} capas en GPU{NC} | {status}")

    try:
        c_layers = input(f"✦ ¿Cuántas capas en GPU deseas asignar? [{preset_layers}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        c_layers = ""
    gpu_layers = c_layers if c_layers else str(preset_layers)

    # Contexto
    print(f"\n{BLUE}╭──────────────────────────────────────────────────────────╮{NC}")
    print(f"{BLUE}│{NC} {YELLOW}📏 TAMAÑO DE CONTEXTO (tokens){NC}                        {BLUE}│{NC}")
    print(f"{BLUE}├──────────────────────────────────────────────────────────┤{NC}")
    print(f"{BLUE}│{NC}  {BOLD}1){NC}  4,096  — Ligero, respuestas cortas")
    print(f"{BLUE}│{NC}  {BOLD}2){NC}  8,192  — Estándar")
    print(f"{BLUE}│{NC}  {BOLD}3){NC} 16,384  — Grande (recomendado)")
    print(f"{BLUE}│{NC}  {BOLD}4){NC} 24,576  — Amplio para razonamiento")
    print(f"{BLUE}│{NC}  {BOLD}5){NC} 32,768  — Muy grande")
    print(f"{BLUE}│{NC}  {BOLD}6){NC} 65,536  — Ultra grande (Claude Code local)")
    print(f"{BLUE}╰──────────────────────────────────────────────────────────╯{NC}")
    print(f"  Actual / Preset: {GREEN}{suggested_ctx}{NC} tokens\n")

    try:
        ctx_opt = input(f"Elige [1-6] o valor numérico (Enter = mantener {suggested_ctx}): ").strip()
    except (EOFError, KeyboardInterrupt):
        ctx_opt = ""

    ctx_map = {"1": "4096", "2": "8192", "3": "16384", "4": "24576", "5": "32768", "6": "65536"}
    new_ctx = ctx_map.get(ctx_opt, ctx_opt if ctx_opt else suggested_ctx)

    # Thinking
    print(f"\n{BLUE}╭──────────────────────────────────────────────────────────╮{NC}")
    print(f"{BLUE}│{NC} {YELLOW}🧠 NIVEL DE THINKING (Reasoning Budget){NC}                {BLUE}│{NC}")
    print(f"{BLUE}├──────────────────────────────────────────────────────────┤{NC}")
    print(f"{BLUE}│{NC}  {BOLD}0){NC} off   — Sin razonamiento (ultra rápido)")
    print(f"{BLUE}│{NC}  {BOLD}1){NC} low   — Budget:  1,024 tokens (rápido)")
    print(f"{BLUE}│{NC}  {BOLD}2){NC} high  — Budget:  8,192 tokens (recomendado)")
    print(f"{BLUE}│{NC}  {BOLD}3){NC} xhigh — Budget: 38,912 tokens (máximo)")
    print(f"{BLUE}╰──────────────────────────────────────────────────────────╯{NC}")
    print(f"  Actual / Preset: {GREEN}{suggested_thinking}{NC}\n")

    try:
        think_opt = input(f"Elige nivel [0-3] (Enter = mantener '{suggested_thinking}'): ").strip()
    except (EOFError, KeyboardInterrupt):
        think_opt = ""

    think_map = {
        "0": ("off", "off"),
        "1": ("on", "low"),
        "2": ("on", "high"),
        "3": ("on", "xhigh"),
    }
    if think_opt in think_map:
        new_reasoning, new_thinking = think_map[think_opt]
    else:
        new_reasoning, new_thinking = suggested_reasoning, suggested_thinking

    # Max tokens
    try:
        max_opt = input(f"✦ Límite de salida (Max Tokens) [{suggested_max}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        max_opt = ""
    new_max = max_opt if max_opt else suggested_max

    # Turbo MTP
    print(f"\n{BLUE}╭──────────────────────────────────────────────────────────╮{NC}")
    print(f"{BLUE}│{NC} {YELLOW}🚀 MODO TURBO / SPECULATIVE DECODING & MTP{NC}             {BLUE}│{NC}")
    print(f"{BLUE}├──────────────────────────────────────────────────────────┤{NC}")
    print(f"{BLUE}│{NC}  {BOLD}0){NC} Desactivado (Estándar)")
    print(f"{BLUE}│{NC}  {BOLD}1){NC} N-Gram Simple (Aceleración sin modelo draft)")
    print(f"{BLUE}│{NC}  {BOLD}2){NC} Draft MTP (Auto-asociado con {final_model_draft or 'MTP'})")
    print(f"{BLUE}│{NC}  {BOLD}3){NC} Draft Model (Modelo borrador auxiliar)")
    print(f"{BLUE}╰──────────────────────────────────────────────────────────╯{NC}")
    spec_desc = f"{final_spec_type} -> {final_model_draft}" if final_model_draft else final_spec_type
    print(f"  Sugerido por Auto-Asociación: {CYAN}{spec_desc}{NC}\n")

    try:
        turbo_opt = input(f"Elige [0-3] (Enter = aceptar sugerido): ").strip()
    except (EOFError, KeyboardInterrupt):
        turbo_opt = ""

    if turbo_opt == "0":
        new_spec_type = "none"
        new_model_draft = ""
        new_draft_n_max = "3"
    elif turbo_opt == "1":
        new_spec_type = "ngram-simple"
        new_model_draft = ""
        new_draft_n_max = "3"
    elif turbo_opt == "2":
        new_spec_type = "draft-mtp"
        new_model_draft = final_model_draft
        new_draft_n_max = final_draft_n
    elif turbo_opt == "3":
        new_spec_type = "draft-simple"
        new_model_draft = final_model_draft or "Qwen3.5-0.8B-UD-Q8_K_XL.gguf"
        new_draft_n_max = final_draft_n
    else:
        new_spec_type = final_spec_type
        new_model_draft = final_model_draft
        new_draft_n_max = final_draft_n

    # Fit VRAM
    try:
        fit_choice = input(f"✦ ¿Activar modo estricto VRAM (--fit off)? (s/n) [{ 's' if preset_fit == 'off' else 'n' }]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        fit_choice = ""

    new_fit = "off" if fit_choice in ["s", "y", "si", "yes"] else ("on" if fit_choice in ["n", "no"] else preset_fit)

    updates = {
        "MODEL_FILE": selected_model,
        "MODEL_REPO": preset.get("MODEL_REPO", f"local/{selected_model}"),
        "AI_GPU_LAYERS": gpu_layers,
        "AI_CTX_SIZE": new_ctx,
        "AI_REASONING": new_reasoning,
        "AI_THINKING_LEVEL": new_thinking,
        "AI_MAX_TOKENS": new_max,
        "AI_SPEC_TYPE": new_spec_type,
        "AI_MODEL_DRAFT": new_model_draft,
        "AI_SPEC_DRAFT_N_MAX": new_draft_n_max,
        "AI_FIT": new_fit,
    }
    if preset_top_p: updates["AI_TOP_P"] = preset_top_p
    if preset_top_k: updates["AI_TOP_K"] = preset_top_k
    if preset_temp: updates["AI_TEMPERATURE"] = preset_temp

    save_env_key(ENV_FILE, updates)
    print(f"\n{GREEN}✅ Configuración guardada en .env ({selected_model}){NC}")

    try:
        restart = input(f"\n{YELLOW}¿Deseas iniciar o reiniciar 'ai-serve' ahora con este modelo? (s/n) [s]: {NC}").strip()
    except (EOFError, KeyboardInterrupt):
        restart = "n"

    if restart.lower() in ["s", "y", ""]:
        print(f"\n✦ Deteniendo servidor anterior...")
        if sys.platform == "win32":
            os.system('taskkill /F /IM llama-server.exe >nul 2>&1')
        else:
            os.system('pkill -f llama-server >/dev/null 2>&1')
        print(f"✦ Iniciando ai-serve...")
        serve_bat = PROJECT_ROOT / "bin" / "ai-serve.bat"
        if sys.platform == "win32" and serve_bat.exists():
            os.system(f'"{serve_bat}"')
        else:
            os.system(f'"{PROJECT_ROOT / "bin" / "ai-serve"}"')
    else:
        print(f"✦ Puedes iniciar el servidor cuando quieras con: {BOLD}ai serve{NC}")


if __name__ == "__main__":
    main()
