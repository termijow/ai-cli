#!/usr/bin/env python3
"""
homelab_daemon.py - Autonomous 24/7 WhatsApp Intelligence & Google Calendar Sync for Ubuntu Server

Features:
1. Runs 100% headless with strict Read-Only security shield on WhatsApp Web.
2. Serves QR code at http://<ip>:3094/whatsapp/qr if initial linking is needed.
3. Periodically inspects monitored contacts or active conversations.
4. Calculates message DELTAS (only new messages since last check) to save CPU/GPU tokens.
5. Feeds deltas to local Qwen 3.6 to extract facts, birthdays, addresses, and events.
6. Automatically creates events in Google Calendar via official API.
7. Continuously updates Obsidian CRM vault (~/Documents/Obsidian_WhatsApp_CRM).
"""

import os
import sys
import time
import json
import asyncio
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.whatsapp_session_exporter import session_exporter
from backend.obsidian_vault_exporter import vault_exporter
from backend.google_calendar_sync import calendar_sync
from backend.whatsapp_analyzer_engine import WhatsAppBatchAnalyzer

# Logging configuration
LOG_DIR = Path.home() / ".ai_cli_whatsapp"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "daemon.log"
STATE_FILE = LOG_DIR / "daemon_state.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    ]
)
logger = logging.getLogger("homelab-daemon")


class HomelabWhatsAppDaemon:
    def __init__(self, check_interval_seconds: int = 900, headless: bool = True):
        self.check_interval = check_interval_seconds
        self.headless = headless
        self.running = False
        self.state: Dict[str, Any] = self._load_state()
        self.analyzer = WhatsAppBatchAnalyzer()

    def _load_state(self) -> Dict[str, Any]:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"No se pudo cargar estado previo: {e}")
        return {"contacts": {}, "last_run": None}

    def _save_state(self):
        try:
            self.state["last_run"] = datetime.now().isoformat()
            STATE_FILE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"Error guardando estado del daemon: {e}")

    async def run(self):
        """Main daemon loop."""
        self.running = True
        logger.info("=" * 60)
        logger.info("🚀 Iniciando Homelab WhatsApp & Google Calendar Daemon")
        logger.info(f"⏱️ Intervalo de revisión: cada {self.check_interval} segundos ({self.check_interval / 60:.1f} minutos)")
        logger.info(f"📁 Directorio de estado: {LOG_DIR}")
        logger.info(f"📓 Bóveda Obsidian: {vault_exporter.vault_path}")
        logger.info("🔒 Modo Seguridad: WhatsApp Web 100% de SOLO LECTURA (cero escritura)")
        logger.info("=" * 60)

        # Setup graceful shutdown handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_shutdown)
            except NotImplementedError:
                pass

        while self.running:
            try:
                await self.execute_cycle()
            except Exception as e:
                logger.error(f"Error en ciclo del daemon: {e}", exc_info=True)

            if not self.running:
                break

            logger.info(f"💤 Esperando {self.check_interval}s para el próximo ciclo...")
            for _ in range(int(self.check_interval)):
                if not self.running:
                    break
                await asyncio.sleep(1)

        logger.info("🛑 Daemon detenido de forma segura.")

    def _handle_shutdown(self):
        logger.info("⚠️ Señal de terminación recibida. Cerrando daemon...")
        self.running = False

    async def execute_cycle(self):
        """Runs a single inspection and sync cycle."""
        logger.info(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo de monitoreo...")

        # 1. Check Google Calendar Status
        gcal_status = calendar_sync.get_status()
        if gcal_status["authenticated"]:
            logger.info("📅 Google Calendar API: Conectado y listo.")
        else:
            logger.info("📅 Google Calendar API: Modo manual / 1-Clic (Falta vincular token.json si deseas auto-sync).")

        # 2. Launch headless browser session to read chats
        # We reuse session_exporter in headless mode
        session_exporter.headless = self.headless

        try:
            logger.info("🌐 Conectando a WhatsApp Web (headless)...")
            export_result = await session_exporter.export_all_chats(
                limit=50,
                max_scrolls_per_chat=5,
                force_reexport=False
            )

            exported_files = export_result.get("exported", [])
            logger.info(f"📊 Resultado del escaneo: {len(exported_files)} chats con mensajes nuevos exportados.")

            # 3. Process new files
            for chat_file in exported_files:
                await self._process_chat_delta(Path(chat_file))

            self._save_state()

        except Exception as e:
            logger.error(f"Error durante la lectura de WhatsApp Web: {e}")

    async def _process_chat_delta(self, chat_path: Path):
        """Processes an exported chat file with local Qwen 3.6."""
        contact_name = chat_path.stem.replace("Chat_de_WhatsApp_con_", "").replace("_", " ")
        logger.info(f"\n🧠 Analizando conversación con: '{contact_name}'...")

        try:
            text = chat_path.read_text(encoding="utf-8")
            lines = [l for l in text.split("\n") if l.strip()]
            current_count = len(lines)

            # Check delta from state
            contact_state = self.state["contacts"].get(contact_name, {})
            last_count = contact_state.get("last_line_count", 0)

            if current_count <= last_count and last_count > 0:
                logger.info(f"  ⏭️ '{contact_name}' no tiene líneas nuevas ({current_count} líneas). Omitiendo.")
                return

            new_lines = lines[last_count:] if last_count > 0 else lines
            logger.info(f"  ⚡ Procesando delta de {len(new_lines)} líneas nuevas para {contact_name}...")

            delta_text = "\n".join(new_lines)

            # Run Qwen 3.6 analysis on the delta
            profile = await self.analyzer.process_conversation(
                delta_text,
                chunk_size=150,
                overlap=20
            )

            # 1. Update Obsidian CRM contact note
            if profile:
                obs_res = vault_exporter.export_contact_profile(profile, contact_filter=contact_name)
                logger.info(f"  📓 Bóveda Obsidian actualizada: {obs_res.get('contact_file', '')}")

                # 2. Check for events/commitments to sync with Google Calendar
                events = profile.get("eventos_y_compromisos", [])
                for ev in events:
                    desc = ev.get("descripcion", "")
                    fecha = ev.get("fecha", "")
                    if desc and fecha:
                        await self._sync_event_to_google_calendar(contact_name, desc, fecha)

            # Update contact state
            self.state["contacts"][contact_name] = {
                "last_line_count": current_count,
                "last_sync": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error procesando delta de {contact_name}: {e}")

    async def _sync_event_to_google_calendar(self, contact_name: str, description: str, date_str: str):
        """Creates event in Google Calendar and records it in Obsidian."""
        title = f"{description} (con {contact_name})"
        logger.info(f"  📅 Detectado compromiso: '{title}' [{date_str}]")

        try:
            res = calendar_sync.create_event(
                title=title,
                start_dt=date_str,
                description=f"Compromiso detectado automáticamente por Qwen 3.6 desde WhatsApp con {contact_name}.\nFecha original: {date_str}",
                location=""
            )

            if res.get("status") == "synced":
                logger.info(f"  ✅ ¡Evento creado automáticamente en Google Calendar! ID: {res.get('event_id')}")
            else:
                logger.info(f"  ℹ️ Evento preparado (1-Clic URL): {res.get('google_calendar_url', '')[:60]}...")

        except Exception as e:
            logger.error(f"Fallo al sincronizar evento en Google Calendar: {e}")


def main():
    interval = 900
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        interval = int(sys.argv[1])
    elif "--interval" in sys.argv:
        idx = sys.argv.index("--interval")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            interval = int(sys.argv[idx + 1])

    daemon = HomelabWhatsAppDaemon(check_interval_seconds=interval, headless=True)
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
