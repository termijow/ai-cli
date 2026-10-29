import time
import os

import json

from pathlib import Path

from typing import List, Dict, Any, Optional



PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARENA_DIR = PROJECT_ROOT / "benchmarks" / "arena"

MODELS_DIR = PROJECT_ROOT / "models"



def find_installed_models():

    found = []

    seen = set()

    if not MODELS_DIR.exists():

        return found

    for f in MODELS_DIR.rglob("*.gguf"):

        n_lower = f.name.lower()

        if any(x in n_lower for x in ["mmproj", "imatrix", "draft", "mtp", "dflash"]):

            continue

        if f.name in seen:

            continue

        seen.add(f.name)

        found.append(f)

    return sorted(found, key=lambda x: x.name)

USER_RATINGS_FILE = ARENA_DIR / "user_ratings.json"

def load_user_ratings() -> Dict[str, Any]:
    if USER_RATINGS_FILE.exists():
        try:
            return json.loads(USER_RATINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_user_rating(model_id: str, stars: int, playable: Optional[bool] = None, review: Optional[str] = None, user_rank: Optional[str] = None) -> Dict[str, Any]:
    ratings = load_user_ratings()
    clean_id = model_id.lower().replace(".gguf", "")

    # Match existing key
    target_key = clean_id
    for k in ratings:
        if k in clean_id or clean_id in k:
            target_key = k
            break

    entry = ratings.get(target_key, {})
    clamped_stars = max(1, min(5, int(stars)))
    entry["stars"] = clamped_stars
    entry["user_rating"] = float(clamped_stars * 2)
    entry["rating_str"] = f"{clamped_stars}/5 ({clamped_stars * 2}/10)"

    if playable is not None:
        entry["playable"] = bool(playable)
    elif "playable" not in entry:
        entry["playable"] = (clamped_stars >= 3)

    if review is not None:
        entry["user_review"] = review.strip()
    elif "user_review" not in entry:
        entry["user_review"] = f"Calificado con {clamped_stars} estrellas por el usuario."

    if user_rank is not None and user_rank.strip():
        entry["user_rank"] = user_rank.strip()
    elif "user_rank" not in entry:
        if clamped_stars >= 5: entry["user_rank"] = "Top 5 Estrellas"
        elif clamped_stars == 4: entry["user_rank"] = "Muy Bueno (4★)"
        elif clamped_stars == 3: entry["user_rank"] = "Aceptable (3★)"
        elif clamped_stars == 2: entry["user_rank"] = "Defectuoso (2★)"
        else: entry["user_rank"] = "Roto / Inutilizable (1★)"

    if clamped_stars >= 5: entry["badge_class"] = "badge-gold"
    elif clamped_stars == 4: entry["badge_class"] = "badge-emerald"
    elif clamped_stars == 3: entry["badge_class"] = "badge-cyan"
    elif clamped_stars == 2: entry["badge_class"] = "badge-amber"
    else: entry["badge_class"] = "badge-rose"

    entry["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    ratings[target_key] = entry

    USER_RATINGS_FILE.write_text(json.dumps(ratings, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry



USER_FEEDBACK_MAP = {

    "qwen3.6-35b": {

        "user_rank": "Top 1 Absoluto",

        "user_rating": 10.0,

        "rating_str": "10/10",

        "user_review": "Funciona perfectamente, se ve hermoso (estética cyberpunk neón impecable), fluido y responsivo.",

        "badge_class": "badge-gold",

        "playable": True

    },

    "nvidia-nemotron-3.5-bolt-e4b": {

        "user_rank": "Top 1 (E4B Turbo)",

        "user_rating": 9.5,

        "rating_str": "9.5/10",

        "user_review": "100/100 en benchmark automatizado. 30.97 tok/s con DFlash MTP. Juego fluido y código impecable.",

        "badge_class": "badge-emerald",

        "playable": True

    },

    "gemma-4-e4b-it-ud-q6_k_xl": {

        "user_rank": "Top 2 (Mejor E4B)",

        "user_rating": 9.0,

        "rating_str": "9/10",

        "user_review": "El modelo compacto que más gustó al usuario. Funciona muy bien, buena jugabilidad y menú responsivo.",

        "badge_class": "badge-cyan",

        "playable": True

    },

    "gemma-4-e4b": {

        "user_rank": "Top 2",

        "user_rating": 8.5,

        "rating_str": "8.5/10",

        "user_review": "Funciona y se ve bien, pero no le gana a Qwen 3.6 35B en refinamiento visual.",

        "badge_class": "badge-cyan",

        "playable": True

    },

    "gemma-4-e2b-it-ud-q6_k_xl": {

        "user_rank": "Defectuoso (Bloqueo UI)",

        "user_rating": 6.0,

        "rating_str": "6/10",

        "user_review": "El juego corre en el fondo pero el menú de inicio se queda bloqueado al frente, no hay cómo cerrarlo.",

        "badge_class": "badge-amber",

        "playable": False

    },

    "gemma-4-e2b": {

        "user_rank": "Defectuoso",

        "user_rating": 5.0,

        "rating_str": "5/10",

        "user_review": "Carga el canvas (7/10 visual), pero la serpiente no se mueve. No jugable.",

        "badge_class": "badge-amber",

        "playable": False

    },

    "ternary-bonsai": {

        "user_rank": "No Jugable",

        "user_rating": 4.0,

        "rating_str": "4/10",

        "user_review": "La UI se ve bonita y funciona, pero la lógica del juego está inactiva.",

        "badge_class": "badge-rose",

        "playable": False

    },

    "gemma-4-26b": {

        "user_rank": "Decepcionante",

        "user_rating": 3.0,

        "rating_str": "3/10",

        "user_review": "Le tenía más fe, pero nada que ver con Qwen 3.6. El juego ni siquiera es jugable.",

        "badge_class": "badge-rose",

        "playable": False

    },

    "qwen3.5-9b": {

        "user_rank": "Roto (Scope Bug)",

        "user_rating": 2.0,

        "rating_str": "2/10",

        "user_review": "Rankea alto en benchmarks sintéticos pero dejó variables fuera de scope provocando ReferenceError.",

        "badge_class": "badge-red",

        "playable": False

    },

    "ling-3.0-tiny": {

        "user_rank": "Pésimo",

        "user_rating": 2.0,

        "rating_str": "2/10",

        "user_review": "Para los tokens que consumió me pareció una remierda. Nivel visual y jugable muy bajo.",

        "badge_class": "badge-red",

        "playable": False

    },

    "qwen3.5-0.8b": {

        "user_rank": "Pésimo",

        "user_rating": 1.0,

        "rating_str": "1/10",

        "user_review": "Demasiado pequeño para un videojuego completo sin alucinaciones.",

        "badge_class": "badge-red",

        "playable": False

    }

}





def get_all_benchmarks(sort_by: str = "score", order: str = "desc", query: str = "", status: str = "all") -> Dict[str, Any]:
    if not ARENA_DIR.exists():
        return {"total": 0, "benchmarks": [], "pending": [], "summary": {}}

    items = []
    total_playable = 0
    benchmarked_folder_names = set()
    user_ratings = load_user_ratings()

    for folder in ARENA_DIR.iterdir():
        if not folder.is_dir():
            continue
        snake_file = folder / "snake.html"
        if not snake_file.exists():
            continue

        benchmarked_folder_names.add(folder.name.lower())

        stats_file = folder / "stats.json"
        stats = {}
        if stats_file.exists():
            try:
                stats = json.loads(stats_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass

        iter_files = list(folder.glob("snake_iter_*.html"))
        iterations = len(iter_files) if iter_files else stats.get("iterations", 1)

        f_lower = folder.name.lower()
        
        # 1. First check user_ratings.json (highest priority)
        matched_rating = None
        for k, v in user_ratings.items():
            if k == f_lower or k in f_lower or f_lower in k:
                matched_rating = v
                break

        # 2. Fall back to USER_FEEDBACK_MAP
        if not matched_rating:
            for k, v in USER_FEEDBACK_MAP.items():
                if k in f_lower or f_lower in k:
                    matched_rating = v
                    break

        score = stats.get("score", 100)
        speed = float(stats.get("speed", 0.0))
        time_s = float(stats.get("time_s", 0.0))
        tokens = int(stats.get("tokens", 0))

        if matched_rating:
            stars = int(matched_rating.get("stars", round(matched_rating.get("user_rating", 6.0) / 2)))
            stars = max(1, min(5, stars))
            user_rank = matched_rating.get("user_rank", "Evaluado")
            user_rating = float(matched_rating.get("user_rating", stars * 2))
            rating_str = matched_rating.get("rating_str", f"{stars}/5")
            user_review = matched_rating.get("user_review", "Evaluado en AI Arena.")
            badge_class = matched_rating.get("badge_class", "badge-cyan")
            is_playable = bool(matched_rating.get("playable", stars >= 3))
        else:
            stars = max(1, min(5, round(score / 20))) if score else 3
            user_rank = "Evaluado"
            user_rating = float(stars * 2)
            rating_str = f"{stars}/5"
            user_review = "Evaluado en Arena Loop Engineering. ¡Califícalo con estrellitas!"
            badge_class = "badge-cyan"
            is_playable = (score >= 70)

        file_size_kb = round(snake_file.stat().st_size / 1024, 1)

        if is_playable:
            total_playable += 1

        entry = {
            "id": folder.name,
            "model": folder.name,
            "score": score,
            "stars": stars,
            "speed_tps": speed,
            "time_sec": time_s,
            "tokens": tokens,
            "iterations": iterations,
            "has_preview": True,
            "has_benchmark": True,
            "status": "completed",
            "file_size_kb": file_size_kb,
            "user_rank": user_rank,
            "user_rating": user_rating,
            "rating_str": rating_str,
            "user_review": user_review,
            "badge_class": badge_class,
            "playable": is_playable,
            "passed_checks": stats.get("passed_checks", []),
            "failed_checks": stats.get("failed_checks", []),
        }

        # Filter query
        if query:
            q = query.lower()
            if q not in folder.name.lower() and q not in user_rank.lower() and q not in user_review.lower():
                continue

        items.append(entry)

    # Sort benchmarked items
    reverse = (order.lower() == "desc")
    if sort_by in ["stars", "estrellas"]:
        items.sort(key=lambda x: (x["stars"], x["user_rating"], x["score"]), reverse=reverse)
    elif sort_by in ["rating", "user_rating"]:
        items.sort(key=lambda x: (x["user_rating"], x["stars"], x["score"]), reverse=reverse)
    elif sort_by in ["score", "puntuacion"]:
        items.sort(key=lambda x: (x["score"], x["stars"], x["user_rating"]), reverse=reverse)
    elif sort_by in ["speed", "speed_tps", "velocidad"]:
        items.sort(key=lambda x: x["speed_tps"], reverse=reverse)
    elif sort_by in ["time", "time_sec", "tiempo"]:
        items.sort(key=lambda x: x["time_sec"], reverse=reverse)
    elif sort_by in ["tokens"]:
        items.sort(key=lambda x: x["tokens"], reverse=reverse)
    elif sort_by in ["name", "model"]:
        items.sort(key=lambda x: x["model"].lower(), reverse=reverse)
    else:
        items.sort(key=lambda x: (x["stars"], x["score"]), reverse=reverse)

    # Detect installed models without benchmark
    installed = find_installed_models()
    pending_items = []
    for m in installed:
        stem = m.stem
        if stem.lower() in benchmarked_folder_names:
            continue
        
        matched_any = False
        for b_name in benchmarked_folder_names:
            if b_name in stem.lower() or stem.lower() in b_name:
                matched_any = True
                break
        if matched_any:
            continue

        size_gb = round(m.stat().st_size / (1024**3), 2)
        
        # Check user rating for pending
        p_rating = None
        for k, v in user_ratings.items():
            if k == stem.lower() or k in stem.lower():
                p_rating = v
                break

        p_stars = p_rating.get("stars", 0) if p_rating else 0
        p_review = p_rating.get("user_review", f"Modelo instalado ({size_gb} GB). Listo para ejecutar benchmark con ai-arena.") if p_rating else f"Modelo instalado ({size_gb} GB). Listo para ejecutar benchmark con ai-arena."

        pending_entry = {
            "id": stem,
            "model": m.name,
            "stem": stem,
            "score": None,
            "stars": p_stars,
            "speed_tps": 0.0,
            "time_sec": 0.0,
            "tokens": 0,
            "iterations": 0,
            "has_preview": False,
            "has_benchmark": False,
            "status": "pending",
            "file_size_gb": size_gb,
            "file_size_kb": round(m.stat().st_size / 1024, 0),
            "user_rank": "Pendiente",
            "user_rating": 0.0,
            "rating_str": f"{p_stars}★ (Sin Evaluar)" if p_stars > 0 else "Sin Evaluar",
            "user_review": p_review,
            "badge_class": "badge-amber",
            "playable": False,
            "passed_checks": [],
            "failed_checks": []
        }

        if query:
            q = query.lower()
            if q not in m.name.lower() and q not in stem.lower():
                continue

        pending_items.append(pending_entry)

    pending_items.sort(key=lambda x: x["model"].lower())

    summary = {
        "total_models": len(items) + len(pending_items),
        "total_benchmarked": len(items),
        "total_pending": len(pending_items),
        "total_playable": total_playable,
        "top_overall": "Qwen 3.6 35B A3B (UD-IQ2_XXS)",
        "top_small": "NVIDIA Nemotron 3.5 Bolt E4B (DFlash MTP)",
        "top_small_user_choice": "Gemma 4 E4B (UD-Q6_K_XL)",
        "hardware": "AMD Radeon RX 6600 (8 GB VRAM)"
    }

    if status in ["completed", "benchmarked"]:
        return {
            "total": len(items),
            "benchmarks": items,
            "pending": [],
            "all": items,
            "summary": summary
        }
    elif status == "pending":
        return {
            "total": len(pending_items),
            "benchmarks": [],
            "pending": pending_items,
            "all": pending_items,
            "summary": summary
        }

    return {
        "total": len(items) + len(pending_items),
        "benchmarks": items,
        "pending": pending_items,
        "all": items + pending_items,
        "summary": summary
    }


def get_model_preview_html(model_name: str) -> Optional[str]:

    target_dir = ARENA_DIR / model_name

    if not target_dir.exists():

        # Match by case-insensitive or substring

        for f in ARENA_DIR.iterdir():

            if f.is_dir() and model_name.lower() in f.name.lower():

                target_dir = f

                break

    

    snake_file = target_dir / "snake.html"

    if snake_file.exists():

        return snake_file.read_text(encoding="utf-8", errors="ignore")

    return None





def render_benchmark_dashboard_html() -> str:

    """Genera la página HTML interactiva standalone con temática Cyberpunk Neon."""

    return """<!DOCTYPE html>

<html lang="es">

<head>

  <meta charset="UTF-8">

  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>AI-CLI Arena Leaderboard & Benchmarks</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">

  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

  <style>

    :root {

      --bg-base: #090d16;

      --bg-card: #0f172a;

      --bg-card-hover: #17223b;

      --border-color: #1e293b;

      --border-glow: rgba(16, 185, 129, 0.35);

      --emerald: #10b981;

      --emerald-glow: 0 0 20px rgba(16, 185, 129, 0.4);

      --cyan: #06b6d4;

      --amber: #f59e0b;

      --rose: #f43f5e;

      --gold: #fbbf24;

      --text-main: #f8fafc;

      --text-muted: #94a3b8;

      --text-sub: #64748b;

      --font-sans: 'Plus Jakarta Sans', system-ui, sans-serif;

      --font-mono: 'JetBrains Mono', monospace;

    }



    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {

      background-color: var(--bg-base);

      color: var(--text-main);

      font-family: var(--font-sans);

      min-height: 100vh;

      display: flex;

      flex-direction: column;

      overflow-x: hidden;

    }



    /* Top glowing bar */

    .top-glow {

      height: 3px;

      background: linear-gradient(90deg, #10b981, #06b6d4, #8b5cf6, #f59e0b, #10b981);

      background-size: 200% 100%;

      animation: gradientMove 6s linear infinite;

    }

    @keyframes gradientMove {

      0% { background-position: 0% 50%; }

      100% { background-position: 200% 50%; }

    }



    /* Container */

    .container {

      max-width: 1320px;

      margin: 0 auto;

      padding: 24px 28px;

      width: 100%;

    }



    /* Header */

    header {

      display: flex;

      justify-content: space-between;

      align-items: center;

      padding-bottom: 24px;

      border-bottom: 1px solid var(--border-color);

      flex-wrap: wrap;

      gap: 16px;

    }



    .brand-group {

      display: flex;

      align-items: center;

      gap: 14px;

    }

    .logo-badge {

      width: 44px;

      height: 44px;

      border-radius: 12px;

      background: linear-gradient(135deg, #10b981 0%, #059669 100%);

      display: flex;

      align-items: center;

      justify-content: center;

      box-shadow: var(--emerald-glow);

      font-size: 22px;

    }

    .title-h1 {

      font-size: 22px;

      font-weight: 800;

      letter-spacing: -0.5px;

      display: flex;

      align-items: center;

      gap: 10px;

    }

    .badge-pill {

      font-size: 11px;

      padding: 3px 8px;

      border-radius: 999px;

      font-weight: 700;

      text-transform: uppercase;

      letter-spacing: 0.5px;

    }

    .badge-emerald { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }

    .badge-gold { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.4); }

    .badge-cyan { background: rgba(6, 182, 212, 0.15); color: #06b6d4; border: 1px solid rgba(6, 182, 212, 0.4); }

    .badge-amber { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); }

    .badge-rose { background: rgba(244, 63, 94, 0.15); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.4); }

    .badge-red { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }



    .subtitle {

      font-size: 13px;

      color: var(--text-muted);

      margin-top: 2px;

    }



    .header-links {

      display: flex;

      gap: 10px;

    }

    .btn {

      padding: 8px 16px;

      border-radius: 8px;

      font-size: 13px;

      font-weight: 600;

      cursor: pointer;

      display: inline-flex;

      align-items: center;

      gap: 8px;

      text-decoration: none;

      transition: all 0.2s ease;

      border: 1px solid var(--border-color);

      background: var(--bg-card);

      color: var(--text-main);

    }

    .btn:hover {

      background: var(--bg-card-hover);

      border-color: var(--emerald);

      box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);

    }

    .btn-primary {

      background: #10b981;

      color: #000;

      border-color: #10b981;

      font-weight: 700;

    }

    .btn-primary:hover {

      background: #059669;

      color: #fff;

    }



    /* KPI Summary Cards */

    .kpi-grid {

      display: grid;

      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));

      gap: 16px;

      margin: 24px 0;

    }

    .kpi-card {

      background: var(--bg-card);

      border: 1px solid var(--border-color);

      border-radius: 12px;

      padding: 16px 20px;

      position: relative;

      overflow: hidden;

      transition: transform 0.2s ease;

    }

    .kpi-card:hover {

      transform: translateY(-2px);

      border-color: rgba(16, 185, 129, 0.5);

    }

    .kpi-label {

      font-size: 12px;

      font-weight: 600;

      color: var(--text-muted);

      text-transform: uppercase;

      letter-spacing: 0.5px;

    }

    .kpi-val {

      font-size: 24px;

      font-weight: 800;

      margin-top: 6px;

      color: var(--text-main);

      display: flex;

      align-items: baseline;

      gap: 8px;

    }

    .kpi-sub {

      font-size: 12px;

      color: var(--text-sub);

      margin-top: 4px;

    }



    /* Control Bar */

    .control-bar {

      background: var(--bg-card);

      border: 1px solid var(--border-color);

      border-radius: 12px;

      padding: 14px 18px;

      display: flex;

      flex-wrap: wrap;

      justify-content: space-between;

      align-items: center;

      gap: 14px;

      margin-bottom: 24px;

    }

    .search-box {

      flex: 1;

      min-width: 240px;

      position: relative;

    }

    .search-input {

      width: 100%;

      background: var(--bg-base);

      border: 1px solid var(--border-color);

      border-radius: 8px;

      padding: 9px 12px 9px 36px;

      color: var(--text-main);

      font-size: 13px;

      outline: none;

      transition: border-color 0.2s;

    }

    .search-input:focus {

      border-color: var(--emerald);

    }

    .search-icon {

      position: absolute;

      left: 12px;

      top: 10px;

      color: var(--text-sub);

    }



    .filter-group {

      display: flex;

      gap: 8px;

      flex-wrap: wrap;

    }

    .filter-btn {

      background: var(--bg-base);

      border: 1px solid var(--border-color);

      color: var(--text-muted);

      padding: 6px 12px;

      border-radius: 6px;

      font-size: 12px;

      cursor: pointer;

      transition: all 0.15s;

    }

    .filter-btn.active {

      background: var(--emerald);

      color: #000;

      border-color: var(--emerald);

      font-weight: 700;

    }



    .sort-group {

      display: flex;

      align-items: center;

      gap: 8px;

    }

    .sort-label {

      font-size: 12px;

      color: var(--text-muted);

      white-space: nowrap;

    }

    .sort-select {

      background: var(--bg-base);

      border: 1px solid var(--border-color);

      color: var(--text-main);

      padding: 6px 12px;

      border-radius: 6px;

      font-size: 12px;

      outline: none;

      cursor: pointer;

    }

    .view-toggle {

      display: flex;

      background: var(--bg-base);

      border: 1px solid var(--border-color);

      border-radius: 6px;

      overflow: hidden;

    }

    .view-btn {

      padding: 6px 12px;

      background: transparent;

      border: none;

      color: var(--text-muted);

      cursor: pointer;

      font-size: 12px;

    }

    .view-btn.active {

      background: var(--border-color);

      color: var(--text-main);

      font-weight: 700;

    }



    /* Cards Grid View */

    .cards-grid {

      display: grid;

      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));

      gap: 20px;

    }

    .model-card {

      background: var(--bg-card);

      border: 1px solid var(--border-color);

      border-radius: 14px;

      padding: 20px;

      display: flex;

      flex-direction: column;

      justify-content: space-between;

      position: relative;

      transition: all 0.2s ease;

    }

    .model-card:hover {

      border-color: rgba(16, 185, 129, 0.4);

      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);

      transform: translateY(-2px);

    }

    .card-top {

      display: flex;

      justify-content: space-between;

      align-items: flex-start;

      gap: 12px;

      margin-bottom: 12px;

    }

    .model-title {

      font-size: 15px;

      font-weight: 700;

      color: var(--text-main);

      line-height: 1.3;

      word-break: break-word;

      font-family: var(--font-mono);

    }

    .score-badge {

      display: flex;

      flex-direction: column;

      align-items: flex-end;

      flex-shrink: 0;

    }

    .score-num {

      font-size: 22px;

      font-weight: 800;

      color: #10b981;

      line-height: 1;

    }

    .score-sub {

      font-size: 10px;

      color: var(--text-sub);

      text-transform: uppercase;

      margin-top: 2px;

    }



    .review-quote {

      background: rgba(15, 23, 42, 0.6);

      border-left: 3px solid #10b981;

      padding: 10px 12px;

      border-radius: 0 8px 8px 0;

      font-size: 12px;

      color: #cbd5e1;

      line-height: 1.45;

      margin: 12px 0;

      font-style: italic;

    }

    .review-quote.broken {

      border-left-color: #f43f5e;

      color: #fda4af;

    }



    .metrics-row {

      display: grid;

      grid-template-columns: repeat(3, 1fr);

      gap: 8px;

      background: var(--bg-base);

      border: 1px solid var(--border-color);

      border-radius: 8px;

      padding: 10px 12px;

      margin: 12px 0;

      font-family: var(--font-mono);

      font-size: 11px;

    }

    .metric-cell {

      display: flex;

      flex-direction: column;

    }

    .metric-cell-label {

      font-size: 9px;

      color: var(--text-sub);

      text-transform: uppercase;

    }

    .metric-cell-val {

      font-size: 13px;

      font-weight: 700;

      color: var(--text-main);

      margin-top: 2px;

    }



    .card-footer {

      display: flex;

      justify-content: space-between;

      align-items: center;

      margin-top: 14px;

      padding-top: 12px;

      border-top: 1px solid var(--border-color);

    }



    /* Table View */

    .table-container {

      background: var(--bg-card);

      border: 1px solid var(--border-color);

      border-radius: 12px;

      overflow-x: auto;

      display: none;

    }

    table {

      width: 100%;

      border-collapse: collapse;

      text-align: left;

      font-size: 13px;

    }

    th {

      background: var(--bg-base);

      padding: 12px 16px;

      font-weight: 700;

      color: var(--text-muted);

      border-bottom: 1px solid var(--border-color);

      font-size: 11px;

      text-transform: uppercase;

      letter-spacing: 0.5px;

      cursor: pointer;

    }

    th:hover {

      color: var(--emerald);

    }

    td {

      padding: 14px 16px;

      border-bottom: 1px solid var(--border-color);

      vertical-align: middle;

    }

    tr:hover td {

      background: var(--bg-card-hover);

    }



    /* Modal Player */

    .modal-backdrop {

      display: none;

      position: fixed;

      top: 0; left: 0; width: 100%; height: 100%;

      background: rgba(0, 0, 0, 0.85);

      backdrop-filter: blur(8px);

      z-index: 100;

      align-items: center;

      justify-content: center;

      padding: 20px;

    }

    .modal-backdrop.active {

      display: flex;

    }

    .modal-box {

      background: var(--bg-card);

      border: 1px solid var(--border-glow);

      box-shadow: 0 0 50px rgba(0, 0, 0, 0.8);

      border-radius: 16px;

      width: 100%;

      max-width: 960px;

      height: 90vh;

      display: flex;

      flex-direction: column;

      overflow: hidden;

      animation: modalPop 0.2s ease-out;

    }

    @keyframes modalPop {

      0% { transform: scale(0.95); opacity: 0; }

      100% { transform: scale(1); opacity: 1; }

    }

    .modal-header {

      padding: 14px 20px;

      display: flex;

      justify-content: space-between;

      align-items: center;

      background: var(--bg-base);

      border-bottom: 1px solid var(--border-color);

    }

    .modal-title {

      font-size: 14px;

      font-weight: 700;

      display: flex;

      align-items: center;

      gap: 10px;

      font-family: var(--font-mono);

    }

    .modal-close {

      background: transparent;

      border: none;

      color: var(--text-muted);

      cursor: pointer;

      font-size: 20px;

      padding: 4px;

    }

    .modal-close:hover {

      color: #fff;

    }

    .modal-iframe {

      flex: 1;

      width: 100%;

      border: none;

      background: #000;

    }



    footer {

      margin-top: auto;

      border-top: 1px solid var(--border-color);

      padding: 16px 28px;

      text-align: center;

      font-size: 12px;

      color: var(--text-sub);

    }

  
    /* Star Rating Widget */
    .star-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin: 10px 0 6px 0;
      padding: 6px 10px;
      background: rgba(251, 191, 36, 0.06);
      border: 1px solid rgba(251, 191, 36, 0.2);
      border-radius: 8px;
    }
    .star-bar-label {
      font-size: 9px;
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 2px;
    }
    .star-group {
      display: inline-flex;
      align-items: center;
      gap: 2px;
    }
    .star-btn {
      font-size: 18px;
      cursor: pointer;
      color: rgba(255, 255, 255, 0.18);
      transition: transform 0.1s ease, color 0.1s ease;
      line-height: 1;
      user-select: none;
    }
    .star-btn.filled {
      color: #fbbf24;
    }
    .star-btn:hover {
      transform: scale(1.3);
      color: #f59e0b;
    }
    .star-val {
      font-size: 11px;
      font-weight: 700;
      color: #fbbf24;
      margin-left: 4px;
    }
    .btn-toggle-playable {
      background: transparent;
      border: 1px solid;
      border-radius: 6px;
      padding: 3px 8px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s;
    }
    .btn-toggle-playable.playable {
      color: #10b981;
      border-color: rgba(16, 185, 129, 0.4);
      background: rgba(16, 185, 129, 0.15);
    }
    .btn-toggle-playable.broken {
      color: #f43f5e;
      border-color: rgba(244, 63, 94, 0.4);
      background: rgba(244, 63, 94, 0.15);
    }
    .btn-edit-note {
      background: transparent;
      border: none;
      color: var(--text-sub);
      cursor: pointer;
      font-size: 12px;
      padding: 2px 4px;
      opacity: 0.7;
    }
    .btn-edit-note:hover {
      opacity: 1;
      color: var(--text-main);
    }
</style>

</head>

<body>

  <div class="top-glow"></div>



  <div class="container">

    <!-- Header -->

    <header>

      <div class="brand-group">

        <div class="logo-badge">⚔️</div>

        <div>

          <div class="title-h1">

            AI-CLI ARENA BENCHMARKS

            <span class="badge-pill badge-emerald">Live Leaderboard</span>

          </div>

          <div class="subtitle">Evaluación TDD & Experiencia Real de Videojuegos Autónomos Embebidos</div>

        </div>

      </div>

      <div class="header-links">

        <a href="/" class="btn">💻 Volver a AI Studio</a>

        <a href="/api/benchmarks?sort_by=score&order=desc" target="_blank" class="btn">🔌 JSON API</a>

      </div>

    </header>



    <!-- KPI Summary Cards -->

    <div class="kpi-grid" id="kpiGrid">

      <div class="kpi-card">

        <div class="kpi-label">🏆 Top 1 Absoluto</div>

        <div class="kpi-val" style="color:#fbbf24;">Qwen 3.6 35B</div>

        <div class="kpi-sub">Puntuación: 95/100 | Calificación: 10/10</div>

      </div>

      <div class="kpi-card">

        <div class="kpi-label">⚡ Top 1 Compacto (E4B)</div>

        <div class="kpi-val" style="color:#10b981;">Nemotron 3.5 Bolt</div>

        <div class="kpi-sub">100/100 Pts | 30.97 t/s con DFlash MTP</div>

      </div>

      <div class="kpi-card">

        <div class="kpi-label">🌟 Top 2 Compacto Favorito</div>

        <div class="kpi-val" style="color:#06b6d4;">Gemma 4 E4B</div>

        <div class="kpi-sub">100/100 Pts | Mejor jugabilidad pequeña</div>

      </div>

      <div class="kpi-card">
        <div class="kpi-label">🎮 Modelos en Arena</div>
        <div class="kpi-val" id="kpiPlayableRate">-- / --</div>
        <div class="kpi-sub" id="kpiHardwareSub">Hardware: AMD Radeon RX 6600 8GB</div>
      </div>

    </div>



    <!-- Controls Toolbar -->

    <div class="control-bar">

      <div class="search-box">

        <span class="search-icon">🔍</span>

        <input type="text" id="searchInput" class="search-input" placeholder="Buscar por modelo (ej: gemma, nemotron, qwen)...">

      </div>



      <div class="filter-group">
        <button class="filter-btn active" data-filter="completed">🏆 Con Benchmark</button>
        <button class="filter-btn" data-filter="pending">⏳ Sin Benchmark</button>
        <button class="filter-btn" data-filter="stars5">⭐ Top Estrellas (4-5★)</button>
        <button class="filter-btn" data-filter="broken">❌ Rotos (1-2★)</button>
        <button class="filter-btn" data-filter="all">Todos</button>
        <button class="filter-btn" data-filter="playable">Solo Jugables</button>
        <button class="filter-btn" data-filter="small">Compactos (E2B/E4B)</button>
      </div>



      <div class="sort-group">

        <span class="sort-label">Ordenar:</span>

        <select id="sortSelect" class="sort-select">

          <option value="score_desc">Puntuación (Mayor a Menor)</option>

          <option value="score_asc">Puntuación (Menor a Mayor)</option>

          <option value="rating_desc">Experiencia Usuario (Top a Peor)</option>

          <option value="speed_desc">Velocidad t/s (Más Rápido)</option>

          <option value="time_asc">Tiempo Generación (Menor)</option>

          <option value="tokens_asc">Tokens Consumidos (Menor)</option>

          <option value="name_asc">Nombre Modelo (A - Z)</option>

        </select>



        <div class="view-toggle">

          <button id="btnViewCards" class="view-btn active" title="Vista Tarjetas">🗂️</button>

          <button id="btnViewTable" class="view-btn" title="Vista Tabla">📊</button>

        </div>

      </div>

    </div>



    <!-- Content Views -->

    <div id="cardsView" class="cards-grid">

      <!-- Dynamic cards rendered by JS -->

    </div>



    <div id="tableView" class="table-container">

      <table>

        <thead>

          <tr>

            <th onclick="changeSort('score')">Pos / Modelo</th>

            <th onclick="changeSort('score')">Puntuación TDD</th>

            <th onclick="changeSort('rating')">Veredicto Usuario</th>

            <th onclick="changeSort('speed')">Velocidad</th>

            <th onclick="changeSort('time')">Tiempo</th>

            <th onclick="changeSort('tokens')">Tokens</th>

            <th>Acción</th>

          </tr>

        </thead>

        <tbody id="tableBody">

          <!-- Dynamic table rows rendered by JS -->

        </tbody>

      </table>

    </div>

  </div>



  <!-- Modal Player -->

  <div id="gameModal" class="modal-backdrop">

    <div class="modal-box">

      <div class="modal-header">

        <div class="modal-title">

          <span>🕹️ Arcade Sandbox:</span>

          <span id="modalModelName" style="color:var(--emerald);"></span>

        </div>

        <div style="display:flex; align-items:center; gap:12px;">

          <a id="modalOpenExternal" href="#" target="_blank" class="btn" style="padding:4px 10px; font-size:11px;">↗ Abrir en Pestaña</a>

          <button class="modal-close" onclick="closeModal()">✕</button>

        </div>

      </div>

      <iframe id="gameIframe" class="modal-iframe" src="about:blank"></iframe>

    </div>

  </div>



  <footer>

    AI-CLI Arena Leaderboard &bull; Harness de Loop Engineering & DOM Test &bull; AMD ROCm Vulkan &bull; FastAPI :3094

  </footer>



  <script>
    let rawBenchmarks = [];
    let rawPending = [];
    let rawSummary = {};
    let activeFilter = 'completed';
    let currentView = 'cards';

    async function loadData() {
      try {
        const sortVal = document.getElementById('sortSelect').value;
        const [sortBy, order] = sortVal.split('_');
        const res = await fetch(`/api/benchmarks?sort_by=${sortBy}&order=${order}`);
        const data = await res.json();
        rawBenchmarks = data.benchmarks || [];
        rawPending = data.pending || [];
        rawSummary = data.summary || {};

        const total = rawSummary.total_models || (rawBenchmarks.length + rawPending.length);
        const benchmarked = rawSummary.total_benchmarked || rawBenchmarks.length;
        const pending = rawSummary.total_pending || rawPending.length;

        document.getElementById('kpiPlayableRate').innerHTML = `<span style="color:#10b981;">${benchmarked}</span> / ${total} <span style="font-size:12px; color:var(--text-sub);">(${pending} pendientes)</span>`;
        const hwSub = document.getElementById('kpiHardwareSub');
        if (hwSub) hwSub.innerHTML = `${benchmarked} Evaluados | ${pending} Pendientes | RX 6600`;

        const btnComp = document.querySelector('[data-filter="completed"]');
        if (btnComp) btnComp.innerText = `🏆 Con Benchmark (${benchmarked})`;
        const btnPend = document.querySelector('[data-filter="pending"]');
        if (btnPend) btnPend.innerText = `⏳ Sin Benchmark (${pending})`;
        const btnAll = document.querySelector('[data-filter="all"]');
        if (btnAll) btnAll.innerText = `Todos (${total})`;

        applyFilterAndRender();
      } catch (err) {
        console.error("Error loading benchmarks:", err);
      }
    }

    function applyFilterAndRender() {
      const q = document.getElementById('searchInput').value.trim().toLowerCase();
      let pool = [];

      if (activeFilter === 'completed') {
        pool = [...rawBenchmarks];
      } else if (activeFilter === 'pending') {
        pool = [...rawPending];
      } else if (activeFilter === 'stars5') {
        pool = rawBenchmarks.filter(b => (b.stars || 0) >= 4);
      } else if (activeFilter === 'broken') {
        pool = rawBenchmarks.filter(b => !b.playable || (b.stars || 0) <= 2);
      } else if (activeFilter === 'playable') {
        pool = rawBenchmarks.filter(b => b.playable);
      } else if (activeFilter === 'small') {
        pool = [...rawBenchmarks, ...rawPending].filter(b => b.model.toLowerCase().includes('e4b') || b.model.toLowerCase().includes('e2b') || b.model.toLowerCase().includes('0.8b') || b.model.toLowerCase().includes('tiny'));
      } else {
        pool = [...rawBenchmarks, ...rawPending];
      }

      if (q) {
        pool = pool.filter(b => 
          b.model.toLowerCase().includes(q) || 
          (b.user_rank && b.user_rank.toLowerCase().includes(q)) || 
          (b.user_review && b.user_review.toLowerCase().includes(q))
        );
      }

      renderCards(pool);
      renderTable(pool);
    }

    async function rateModel(modelId, stars) {
      const target = [...rawBenchmarks, ...rawPending].find(x => x.id === modelId || x.model === modelId);
      if (target) {
        target.stars = stars;
        target.rating_str = `${stars}/5 (${stars*2}/10)`;
        if (stars >= 5) target.user_rank = "Top 5 Estrellas";
        else if (stars === 4) target.user_rank = "Muy Bueno (4★)";
        else if (stars === 3) target.user_rank = "Aceptable (3★)";
        else if (stars === 2) target.user_rank = "Defectuoso (2★)";
        else target.user_rank = "Roto / Inútil (1★)";
      }
      applyFilterAndRender();
      try {
        await fetch(`/api/benchmarks/${modelId}/rating`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stars: stars })
        });
      } catch (err) {
        console.error("Error rating model:", err);
      }
    }

    async function togglePlayable(modelId) {
      const target = [...rawBenchmarks, ...rawPending].find(x => x.id === modelId || x.model === modelId);
      if (!target) return;
      target.playable = !target.playable;
      applyFilterAndRender();
      try {
        await fetch(`/api/benchmarks/${modelId}/rating`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stars: target.stars || 3, playable: target.playable })
        });
      } catch (err) {
        console.error("Error toggling playable:", err);
      }
    }

    async function editReview(modelId) {
      const target = [...rawBenchmarks, ...rawPending].find(x => x.id === modelId || x.model === modelId);
      const curr = target ? (target.user_review || '') : '';
      const newRev = prompt('Tu opinión sobre este modelo (ej: 100/100 sintético pero la serpiente no se mueve):', curr);
      if (newRev !== null && newRev.trim()) {
        if (target) target.user_review = newRev.trim();
        applyFilterAndRender();
        try {
          await fetch(`/api/benchmarks/${modelId}/rating`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stars: (target ? target.stars : 3), review: newRev.trim() })
          });
        } catch (err) {
          console.error("Error editing review:", err);
        }
      }
    }

    function copyCliCommand(modelId) {
      const cmd = `ai-arena --model ${modelId}`;
      navigator.clipboard.writeText(cmd);
      alert(`Comando copiado al portapapeles:\n${cmd}`);
    }

    function renderCards(list) {
      const container = document.getElementById('cardsView');
      if (list.length === 0) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--text-sub);">No se encontraron modelos con los filtros seleccionados.</div>`;
        return;
      }

      container.innerHTML = list.map((b) => {
        if (b.status === 'pending') {
          return `
            <div class="model-card" style="border: 1px dashed rgba(245, 158, 11, 0.45);">
              <div>
                <div class="card-top">
                  <div style="flex:1;">
                    <span class="badge-pill badge-amber" style="margin-bottom:6px; display:inline-block;">⏳ Pendiente de Benchmark</span>
                    <h3 class="model-title">${b.model}</h3>
                  </div>
                  <div class="score-badge" style="border-color: rgba(245, 158, 11, 0.4);">
                    <span class="score-num" style="color:var(--amber);">--</span>
                    <span class="score-sub">Sin Evaluar</span>
                  </div>
                </div>

                <div class="review-quote broken">
                  "${b.user_review}"
                </div>

                <div class="metrics-row">
                  <div class="metric-cell">
                    <span class="metric-cell-label">Tamaño</span>
                    <span class="metric-cell-val" style="color:#06b6d4;">${b.file_size_gb} GB</span>
                  </div>
                  <div class="metric-cell">
                    <span class="metric-cell-label">Estado</span>
                    <span class="metric-cell-val" style="color:var(--amber);">Por Evaluar</span>
                  </div>
                  <div class="metric-cell">
                    <span class="metric-cell-label">Harness</span>
                    <span class="metric-cell-val" style="font-size:11px; color:var(--text-muted);">ai-arena</span>
                  </div>
                </div>
              </div>

              <div class="card-footer">
                <span class="badge-pill badge-amber">⏳ Sin Benchmark</span>
                <button class="btn" style="padding:6px 12px; font-size:12px;" onclick="copyCliCommand('${b.id}')">
                  📋 Copiar Comando
                </button>
              </div>
            </div>
          `;
        }

        const speedStr = b.speed_tps > 0 ? `${b.speed_tps.toFixed(1)} t/s` : 'N/A';
        const timeStr = b.time_sec > 0 ? `${b.time_sec.toFixed(0)} s` : 'N/A';
        const tokensStr = b.tokens > 0 ? b.tokens.toLocaleString() : 'N/A';
        const starsNum = b.stars || 0;
        const starsHtml = [1, 2, 3, 4, 5].map(st => `
          <span class="star-btn ${st <= starsNum ? 'filled' : ''}" onclick="rateModel('${b.id}', ${st})" title="Calificar ${st} estrellas">★</span>
        `).join('');

        return `
          <div class="model-card">
            <div>
              <div class="card-top">
                <div style="flex:1;">
                  <span class="badge-pill ${b.badge_class}" style="margin-bottom:6px; display:inline-block;">${b.user_rank}</span>
                  <h3 class="model-title">${b.model}</h3>
                </div>
                <div class="score-badge">
                  <span class="score-num">${b.score}</span>
                  <span class="score-sub">TDD Pts</span>
                </div>
              </div>

              <!-- Interactive Star Bar -->
              <div class="star-bar">
                <div>
                  <div class="star-bar-label">Tu Calificación:</div>
                  <div class="star-group">
                    ${starsHtml}
                    <span class="star-val">${starsNum > 0 ? starsNum + '★' : 'Sin Calificar'}</span>
                  </div>
                </div>
                <button class="btn-toggle-playable ${b.playable ? 'playable' : 'broken'}" onclick="togglePlayable('${b.id}')" title="Click para alternar si realmente funciona o está roto">
                  ${b.playable ? '✓ Jugable' : '❌ Roto'}
                </button>
              </div>

              <!-- User Review Note -->
              <div class="review-quote ${b.playable ? '' : 'broken'}" style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
                <span style="flex:1;">"${b.user_review}"</span>
                <button class="btn-edit-note" onclick="editReview('${b.id}')" title="Editar tu opinión">✏️</button>
              </div>

              <div class="metrics-row">
                <div class="metric-cell">
                  <span class="metric-cell-label">Velocidad</span>
                  <span class="metric-cell-val" style="color:#10b981;">${speedStr}</span>
                </div>
                <div class="metric-cell">
                  <span class="metric-cell-label">Tiempo</span>
                  <span class="metric-cell-val">${timeStr}</span>
                </div>
                <div class="metric-cell">
                  <span class="metric-cell-label">Tokens</span>
                  <span class="metric-cell-val">${tokensStr}</span>
                </div>
              </div>
            </div>

            <div class="card-footer">
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="badge-pill ${b.playable ? 'badge-emerald' : 'badge-rose'}">
                  ${b.playable ? '✓ 100% Jugable' : '❌ Defectuoso'}
                </span>
                <span style="font-size:11px; color:var(--text-sub);">${b.rating_str}</span>
              </div>
              <button class="btn btn-primary" onclick="openGameModal('${b.model}')">
                🎮 Probar Juego
              </button>
            </div>
          </div>
        `;
      }).join('');
    }

    function renderTable(list) {
      const tbody = document.getElementById('tableBody');
      if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-sub);">Sin resultados.</td></tr>`;
        return;
      }

      tbody.innerHTML = list.map((b) => {
        if (b.status === 'pending') {
          return `
            <tr style="opacity:0.85;">
              <td>
                <div style="font-weight:700; font-family:var(--font-mono);">${b.model}</div>
                <div style="font-size:11px; color:var(--amber);">Modelo instalado (${b.file_size_gb} GB) &bull; Pendiente de benchmark</div>
              </td>
              <td><span style="font-size:16px; font-weight:800; color:var(--amber);">--</span>/100</td>
              <td><span class="badge-pill badge-amber">⏳ Pendiente</span></td>
              <td style="color:var(--text-sub); font-family:var(--font-mono); font-size:12px;">N/A</td>
              <td style="color:var(--text-sub); font-family:var(--font-mono); font-size:12px;">N/A</td>
              <td style="color:var(--text-sub); font-family:var(--font-mono); font-size:12px;">N/A</td>
              <td>
                <button class="btn" style="padding:4px 8px; font-size:11px;" onclick="copyCliCommand('${b.id}')">
                  📋 Comando
                </button>
              </td>
            </tr>
          `;
        }

        const speedStr = b.speed_tps > 0 ? `${b.speed_tps.toFixed(1)} t/s` : 'N/A';
        const timeStr = b.time_sec > 0 ? `${b.time_sec.toFixed(0)} s` : 'N/A';
        const tokensStr = b.tokens > 0 ? b.tokens.toLocaleString() : 'N/A';
        const starsNum = b.stars || 0;
        const starsHtml = [1, 2, 3, 4, 5].map(st => `
          <span class="star-btn ${st <= starsNum ? 'filled' : ''}" onclick="rateModel('${b.id}', ${st})" style="font-size:15px;">★</span>
        `).join('');

        return `
          <tr>
            <td>
              <div style="font-weight:700; font-family:var(--font-mono);">${b.model}</div>
              <div style="font-size:11px; color:var(--text-sub);">${(b.user_review || '').substring(0, 50)}...</div>
            </td>
            <td>
              <span style="font-size:16px; font-weight:800; color:#10b981;">${b.score}</span>/100
            </td>
            <td>
              <div style="display:flex; flex-direction:column; gap:4px;">
                <div class="star-group">${starsHtml} <span class="star-val">${starsNum}★</span></div>
                <div style="display:flex; align-items:center; gap:6px;">
                  <span class="badge-pill ${b.badge_class}">${b.user_rank}</span>
                  <button class="btn-toggle-playable ${b.playable ? 'playable' : 'broken'}" style="padding:2px 6px; font-size:10px;" onclick="togglePlayable('${b.id}')">
                    ${b.playable ? '✓ Jugable' : '❌ Roto'}
                  </button>
                </div>
              </div>
            </td>
            <td style="color:#10b981; font-family:var(--font-mono); font-weight:600;">${speedStr}</td>
            <td style="font-family:var(--font-mono);">${timeStr}</td>
            <td style="font-family:var(--font-mono);">${tokensStr}</td>
            <td>
              <button class="btn btn-primary" style="padding:5px 10px; font-size:11px;" onclick="openGameModal('${b.model}')">
                🎮 Jugar
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function openGameModal(model) {
      const url = `/api/benchmarks/${model}/preview`;
      document.getElementById('modalModelName').innerText = model;
      document.getElementById('modalOpenExternal').href = url;
      document.getElementById('gameIframe').src = url;
      document.getElementById('gameModal').classList.add('active');
    }

    function closeModal() {
      document.getElementById('gameModal').classList.remove('active');
      document.getElementById('gameIframe').src = 'about:blank';
    }

    document.getElementById('searchInput').addEventListener('input', applyFilterAndRender);
    document.getElementById('sortSelect').addEventListener('change', loadData);

    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        activeFilter = e.target.dataset.filter;
        applyFilterAndRender();
      });
    });

    document.getElementById('btnViewCards').addEventListener('click', () => {
      document.getElementById('btnViewCards').classList.add('active');
      document.getElementById('btnViewTable').classList.remove('active');
      document.getElementById('cardsView').style.display = 'grid';
      document.getElementById('tableView').style.display = 'none';
      currentView = 'cards';
    });

    document.getElementById('btnViewTable').addEventListener('click', () => {
      document.getElementById('btnViewTable').classList.add('active');
      document.getElementById('btnViewCards').classList.remove('active');
      document.getElementById('cardsView').style.display = 'none';
      document.getElementById('tableView').style.display = 'block';
      currentView = 'table';
    });

    function changeSort(field) {
      const current = document.getElementById('sortSelect').value;
      if (current === `${field}_desc`) {
        document.getElementById('sortSelect').value = `${field}_asc`;
      } else {
        document.getElementById('sortSelect').value = `${field}_desc`;
      }
      loadData();
    }

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });

    loadData();
  </script></script>
</body>

</html>

"""

