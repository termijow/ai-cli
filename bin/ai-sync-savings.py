#!/usr/bin/env python3
"""
ai-sync-savings.py - Synchronize Qwen CLI & AI-CLI token usage and savings
Automatically scans ~/.qwen/projects/*/chats/*.jsonl for completed/in-progress
sessions, extracts token usage (main agent + subagents), calculates simulated savings
against Claude Fable 5 pricing, and records them in SQLite (~/.ai_cli_db.db)
and ~/.ai_cli_savings.
"""

import argparse
import glob
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Claude Fable 5 pricing reference
INPUT_PRICE_PER_TOKEN = 0.0000100   # $10.00 / 1M tokens
OUTPUT_PRICE_PER_TOKEN = 0.0000500  # $50.00 / 1M tokens

DB_FILE = Path.home() / ".ai_cli_db.db"
SAVINGS_FILE = Path.home() / ".ai_cli_savings"
HISTORY_DIR = Path.home() / ".ai_cli_history"
HISTORY_FILE = HISTORY_DIR / "queries.jsonl"
QWEN_PROJECTS_DIR = Path.home() / ".qwen" / "projects"

# Cutoff timestamp for baseline historical sessions (before today)
BASELINE_CUTOFF = "2026-08-28T00:00:00Z"


def init_db(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            input_cost REAL DEFAULT 0.00,
            output_savings REAL DEFAULT 0.00,
            total_savings REAL DEFAULT 0.00
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imported_sessions (
            session_id TEXT PRIMARY KEY,
            last_input_tokens INTEGER DEFAULT 0,
            last_output_tokens INTEGER DEFAULT 0,
            last_savings REAL DEFAULT 0.0,
            updated_at TEXT
        );
    """)
    conn.commit()


def get_current_savings() -> float:
    if SAVINGS_FILE.exists():
        try:
            return float(SAVINGS_FILE.read_text().strip())
        except Exception:
            pass
    if DB_FILE.exists():
        try:
            with sqlite3.connect(str(DB_FILE)) as conn:
                res = conn.execute("SELECT COALESCE(MAX(total_savings), 0.0) FROM usage_logs").fetchone()
                if res and res[0]:
                    return float(res[0])
        except Exception:
            pass
    return 0.0


def set_current_savings(amount: float):
    SAVINGS_FILE.write_text(f"{amount:.2f}\n")


def parse_chat_session(jsonl_path: Path):
    """
    Parse a Qwen chat JSONL file and return (session_id, input_tokens, output_tokens, cached_tokens, last_timestamp).
    Includes tokens from all api_response events (main agent and subagents).
    """
    session_id = jsonl_path.stem
    total_in = 0
    total_out = 0
    total_cached = 0
    last_timestamp = None

    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    ui_event = data.get("systemPayload", {}).get("uiEvent", {})
                    if ui_event.get("event.name") == "qwen-code.api_response":
                        total_in += ui_event.get("input_token_count", 0)
                        total_out += ui_event.get("output_token_count", 0)
                        total_cached += ui_event.get("cached_content_token_count", 0)
                        ts = ui_event.get("event.timestamp") or data.get("timestamp")
                        if ts:
                            last_timestamp = ts
                except Exception:
                    continue
    except Exception as e:
        return None

    return {
        "session_id": session_id,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cached_tokens": total_cached,
        "last_timestamp": last_timestamp,
        "path": str(jsonl_path)
    }


def sync_qwen_sessions(quiet: bool = False, force_all: bool = False):
    if not QWEN_PROJECTS_DIR.exists():
        if not quiet:
            print(f"Directorio de proyectos Qwen no encontrado: {QWEN_PROJECTS_DIR}")
        return 0

    with sqlite3.connect(str(DB_FILE)) as conn:
        init_db(conn)
        cursor = conn.cursor()

        # Check if imported_sessions is completely empty (first run initialization)
        existing_imports = {}
        rows = cursor.execute("SELECT session_id, last_input_tokens, last_output_tokens, last_savings FROM imported_sessions").fetchall()
        is_first_run = (len(rows) == 0)

        for row in rows:
            existing_imports[row[0]] = {
                "last_input_tokens": row[1],
                "last_output_tokens": row[2],
                "last_savings": row[3]
            }

        chat_files = [Path(p) for p in glob.glob(str(QWEN_PROJECTS_DIR / "*" / "chats" / "*.jsonl"))]
        
        # Sort files by modification time so older sessions are processed first
        chat_files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0)

        current_total_savings = get_current_savings()
        synced_count = 0
        total_tokens_added = 0
        total_savings_added = 0.0

        for chat_file in chat_files:
            info = parse_chat_session(chat_file)
            if not info:
                continue

            session_id = info["session_id"]
            curr_in = info["input_tokens"]
            curr_out = info["output_tokens"]
            last_ts = info["last_timestamp"] or datetime.now(timezone.utc).isoformat()

            # If it's the first time seeding and not force_all:
            # Baseline sessions prior to BASELINE_CUTOFF are marked as already accounted for
            if is_first_run and not force_all:
                if last_ts < BASELINE_CUTOFF:
                    cursor.execute(
                        "REPLACE INTO imported_sessions (session_id, last_input_tokens, last_output_tokens, last_savings, updated_at) VALUES (?, ?, ?, ?, ?)",
                        (session_id, curr_in, curr_out, 0.0, last_ts)
                    )
                    continue

            # Calculate deltas
            prev_record = existing_imports.get(session_id)
            if prev_record:
                delta_in = max(0, curr_in - prev_record["last_input_tokens"])
                delta_out = max(0, curr_out - prev_record["last_output_tokens"])
            else:
                delta_in = curr_in
                delta_out = curr_out

            if delta_in == 0 and delta_out == 0:
                continue

            # Calculate savings
            input_cost = delta_in * INPUT_PRICE_PER_TOKEN
            output_cost = delta_out * OUTPUT_PRICE_PER_TOKEN
            delta_saving = input_cost + output_cost

            current_total_savings = round(current_total_savings + delta_saving, 2)

            # Format local timestamp for SQLite & queries.jsonl
            try:
                dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00")).astimezone()
                local_ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                local_ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert into usage_logs
            cursor.execute(
                """INSERT INTO usage_logs 
                   (created_at, input_tokens, output_tokens, input_cost, output_savings, total_savings)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (local_ts_str, delta_in, delta_out, round(input_cost, 4), round(output_cost, 4), current_total_savings)
            )

            # Update imported_sessions
            cursor.execute(
                """REPLACE INTO imported_sessions 
                   (session_id, last_input_tokens, last_output_tokens, last_savings, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, curr_in, curr_out, round(delta_saving, 4), last_ts)
            )
            existing_imports[session_id] = {
                "last_input_tokens": curr_in,
                "last_output_tokens": curr_out,
                "last_savings": round(delta_saving, 4)
            }

            # Append to queries.jsonl
            HISTORY_DIR.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": local_ts_str,
                "query_type": "qwen",
                "session_id": session_id,
                "prompt_tokens": delta_in,
                "completion_tokens": delta_out,
                "savings": round(delta_saving, 4),
                "total_savings": current_total_savings
            }
            try:
                with open(HISTORY_FILE, "a", encoding="utf-8") as hf:
                    hf.write(json.dumps(entry) + "\n")
            except Exception:
                pass

            synced_count += 1
            total_tokens_added += (delta_in + delta_out)
            total_savings_added += delta_saving

            if not quiet:
                short_id = session_id[:8]
                print(f"✨ Sincronizada sesión {short_id}... | +{delta_in:,} in / +{delta_out:,} out | +${delta_saving:.4f} USD")

        conn.commit()

        if synced_count > 0:
            set_current_savings(current_total_savings)
            if not quiet:
                print(f"\n💰 Total Ahorrado actualizado: ${current_total_savings:.2f} USD (+${total_savings_added:.4f} USD)")
                print(f"📊 Tokens nuevos registrados: {total_tokens_added:,} tokens en {synced_count} sesión(es).")
        elif not quiet:
            print("✓ Alcancía al día: no hay nuevas consultas de Qwen pendientes por sincronizar.")

        return synced_count


def main():
    parser = argparse.ArgumentParser(description="Sincronizar uso y ahorro de Qwen con AI-CLI")
    parser.add_argument("-q", "--quiet", action="store_true", help="Modo silencioso (sin salida en consola si todo está bien)")
    parser.add_argument("--force-all", action="store_true", help="Forzar reimportación de todas las sesiones históricas")
    args = parser.parse_args()

    sync_qwen_sessions(quiet=args.quiet, force_all=args.force_all)


if __name__ == "__main__":
    main()
