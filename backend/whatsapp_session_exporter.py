#!/usr/bin/env python3
"""
whatsapp_session_exporter.py - WhatsApp Web Session & Chat Exporter using Playwright

Provides:
1. Interactive WhatsApp Web session manager with persistent profile in ~/.ai_cli_whatsapp_session.
2. QR Code scan handling on initial setup.
3. Message history extractor from active chat or top contacts.
4. Serializer into standard WhatsApp .txt format for LargeChatAnalyzer and Obsidian CRM.
"""

import os
import re
import sys
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

SESSION_DIR = Path.home() / ".ai_cli_whatsapp_session"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

CHATS_EXPORT_DIR = PROJECT_ROOT / "chats"
CHATS_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


class WhatsAppSessionExporter:
    """
    Automates WhatsApp Web interaction with a persistent profile to extract conversations.
    """

    def __init__(self, headless: bool = False, session_dir: Optional[Path] = None):
        self.headless = headless
        self.session_dir = session_dir or SESSION_DIR
        self.browser_context = None

    def export_chat_from_text(self, text_content: str, contact_name: str) -> Path:
        """Saves text content to chats/<contact_name>.txt."""
        safe_name = re.sub(r"[^\w\s-]", "", contact_name).strip().replace(" ", "_")
        output_file = CHATS_EXPORT_DIR / f"Chat_de_WhatsApp_con_{safe_name}.txt"
        output_file.write_text(text_content, encoding="utf-8")
        return output_file

    async def open_interactive_session(self, target_contact: Optional[str] = None, max_scrolls: int = 15) -> Optional[Path]:
        """
        Launches WhatsApp Web with the persistent session.
        If not logged in, allows user to scan the QR code.
        If target_contact is provided, selects it and extracts its messages.
        """
        from playwright.async_api import async_playwright

        print("\n🌐 Iniciando WhatsApp Web con perfil persistente...")
        print(f"📁 Directorio de sesión: {self.session_dir}")

        async with async_playwright() as p:
            # Launch persistent browser context (Chromium)
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.session_dir),
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled"
                ],
                viewport={"width": 1280, "height": 900}
            )

            page = context.pages[0] if context.pages else await context.new_page()

            print("⏳ Navegando a https://web.whatsapp.com...")
            await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

            # Check if user needs to scan QR
            print("\n📱 Verificando estado de sesión...")
            try:
                # Wait for main pane (logged in) or canvas (QR code)
                logged_in_selector = "div#pane-side, div[data-tab='3'], header"
                qr_selector = "canvas[aria-label='Scan this QR code to link a device'], canvas"

                start_time = time.time()
                while time.time() - start_time < 120:
                    if await page.query_selector(logged_in_selector):
                        print("✅ ¡Sesión de WhatsApp Web activa y autenticada!")
                        break
                    elif await page.query_selector(qr_selector):
                        print("📸 Por favor, escanea el código QR en la ventana del navegador con tu teléfono...")
                    await asyncio.sleep(2)
                else:
                    print("⚠️ Tiempo de espera agotado para el escaneo del QR.")
                    await context.close()
                    return None

            except Exception as e:
                print(f"Error al verificar estado de sesión: {e}")

            # If target contact specified, search for it
            chat_title = target_contact or "Chat_Activo"
            if target_contact:
                print(f"\n🔍 Buscando chat con: '{target_contact}'...")
                try:
                    search_box = await page.wait_for_selector(
                        "div[contenteditable='true'][data-tab='3'], div[role='textbox']",
                        timeout=10000
                    )
                    if search_box:
                        await search_box.click()
                        await search_box.fill(target_contact)
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(3)
                except Exception as e:
                    print(f"No se pudo seleccionar automáticamente el contacto: {e}")

            print("\n📜 Leyendo conversación abierta y cargando historial...")
            # Scroll up inside the chat pane to load message history
            try:
                message_pane = await page.wait_for_selector("div[data-tab='8'], div.copyable-area", timeout=10000)
                for s in range(max_scrolls):
                    await page.keyboard.press("PageUp")
                    await asyncio.sleep(0.3)
            except Exception:
                pass

            # Extract messages
            messages = await self._extract_messages_from_page(page)
            print(f"✓ Se extrajeron {len(messages)} mensajes de la conversación.")

            # Detect chat header title if available
            try:
                header_elem = await page.query_selector("header span[title]")
                if header_elem:
                    detected_title = await header_elem.get_attribute("title")
                    if detected_title:
                        chat_title = detected_title
            except Exception:
                pass

            # Format into standard WhatsApp text
            formatted_text = self._format_as_whatsapp_txt(messages, chat_title)
            output_file = self.export_chat_from_text(formatted_text, chat_title)
            print(f"💾 Conversación exportada exitosamente a:\n   {output_file}")

            await context.close()
            return output_file

    async def _extract_messages_from_page(self, page) -> List[Dict[str, str]]:
        """Extracts text messages, timestamps, and senders from the DOM."""
        extracted = []
        try:
            # Query all message containers
            msg_nodes = await page.query_selector_all("div.message-in, div.message-out")
            now_date = datetime.now().strftime("%d/%m/%Y")

            for node in msg_nodes:
                class_attr = await node.get_attribute("class") or ""
                is_out = "message-out" in class_attr
                sender = "Yo" if is_out else "Contacto"

                # Text content
                text_elem = await node.query_selector("span.selectable-text")
                text = await text_elem.inner_text() if text_elem else ""

                if not text:
                    continue

                # Time
                time_elem = await node.query_selector("div[data-pre-plain-text]")
                meta = await time_elem.get_attribute("data-pre-plain-text") if time_elem else ""

                time_str = "12:00"
                if meta:
                    # e.g. [12:30, 27/08/2026] Felipe:
                    m = re.search(r"\[(\d{1,2}:\d{2}(?::\d{2})?),?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?\]\s*([^:]+)?", meta)
                    if m:
                        time_str = m.group(1)
                        if m.group(2):
                            now_date = m.group(2)
                        if m.group(3) and not is_out:
                            sender = m.group(3).strip()

                extracted.append({
                    "date": now_date,
                    "time": time_str,
                    "sender": sender,
                    "text": text.strip()
                })

        except Exception as e:
            print(f"Error extrayendo mensajes del DOM: {e}")

        return extracted

    def _format_as_whatsapp_txt(self, messages: List[Dict[str, str]], chat_title: str) -> str:
        """Formats extracted messages list into standard WhatsApp .txt format."""
        lines = []
        for m in messages:
            lines.append(f"{m['date']}, {m['time']} - {m['sender']}: {m['text']}")
        return "\n".join(lines)


session_exporter = WhatsAppSessionExporter()
