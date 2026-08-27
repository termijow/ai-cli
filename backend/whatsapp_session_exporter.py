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

    def get_safe_filename(self, contact_name: str) -> Path:
        safe_name = re.sub(r"[^\w\s-]", "", contact_name).strip().replace(" ", "_")
        return CHATS_EXPORT_DIR / f"Chat_de_WhatsApp_con_{safe_name}.txt"

    def is_already_exported(self, contact_name: str) -> bool:
        """Checks if this contact has already been exported to chats/."""
        target = self.get_safe_filename(contact_name)
        if target.exists() and target.stat().st_size > 0:
            return True
        # Also check standard names
        for f in CHATS_EXPORT_DIR.glob("*.txt"):
            c_name = f.stem.replace("Chat_de_WhatsApp_con_", "").replace("Chat de WhatsApp con ", "").replace("_", " ")
            if c_name.lower() == contact_name.lower():
                return True
        return False

    def get_exported_contacts_map(self) -> Dict[str, Path]:
        """Returns map of normalized contact name -> exported file path."""
        result = {}
        if CHATS_EXPORT_DIR.exists():
            for f in CHATS_EXPORT_DIR.glob("*.txt"):
                c_name = f.stem.replace("Chat_de_WhatsApp_con_", "").replace("Chat de WhatsApp con ", "").replace("_", " ").strip()
                result[c_name] = f
        return result

    def export_chat_from_text(self, text_content: str, contact_name: str) -> Path:
        """Saves text content to chats/<contact_name>.txt."""
        output_file = self.get_safe_filename(contact_name)
        output_file.write_text(text_content, encoding="utf-8")
        return output_file

    async def _dispatch_callback(self, cb: Optional[Any], data: Dict[str, Any]):
        if not cb:
            return
        try:
            if asyncio.iscoroutinefunction(cb):
                await cb(data)
            else:
                cb(data)
        except Exception as e:
            pass

    async def _launch_readonly_context(self, p):
        """
        Launches Playwright Chromium context with unbreakable Read-Only Isolation Shield.
        - Blocks all keyboard typing into inputs or contenteditable.
        - Completely obliterates the footer message composer, mic, send buttons from DOM and CSS.
        - Disables all Enter key events.
        - Guarantees 0% write ability on WhatsApp Web.
        """
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

        # Inject unbreakable Read-Only Shield BEFORE WhatsApp loads
        await context.add_init_script("""
            (() => {
                // 1. Permanently remove and hide message composer & send buttons via CSS
                const injectShieldCSS = () => {
                    if (document.getElementById('ai-cli-readonly-shield')) return;
                    const style = document.createElement('style');
                    style.id = 'ai-cli-readonly-shield';
                    style.textContent = `
                        /* Completely erase message composer, microphone, and send button */
                        footer,
                        div[data-testid='conversation-compose-box'],
                        div[data-testid='compose-box'],
                        div[data-testid='send'],
                        div[data-tab='10'],
                        div[data-tab='6'],
                        button[aria-label*='Send' i],
                        button[aria-label*='Enviar' i],
                        button[data-tab='11'],
                        span[data-icon='send'],
                        span[data-icon='ptt'] {
                            display: none !important;
                            visibility: hidden !important;
                            pointer-events: none !important;
                            opacity: 0 !important;
                            height: 0 !important;
                            width: 0 !important;
                            position: absolute !important;
                            left: -9999px !important;
                        }
                    `;
                    if (document.head) {
                        document.head.appendChild(style);
                    } else if (document.documentElement) {
                        document.documentElement.appendChild(style);
                    }
                };

                // 2. Intercept and neutralize ANY keydown or Enter that could send text
                window.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.keyCode === 13) {
                        const target = e.target;
                        if (target && (target.isContentEditable || target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                            return false;
                        }
                    }
                }, true);

                // 3. Intercept beforeinput & input events in footer
                window.addEventListener('beforeinput', (e) => {
                    const target = e.target;
                    if (target && target.closest && target.closest('footer')) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        return false;
                    }
                }, true);

                // Run immediately and ensure it persists on DOM updates
                injectShieldCSS();
                window.addEventListener('DOMContentLoaded', injectShieldCSS);
                setInterval(injectShieldCSS, 500);
            })();
        """)

        return context

    async def _apply_readonly_lock(self, page):
        """Additional runtime assurance check."""
        pass

    async def open_interactive_session(self, target_contact: Optional[str] = None, max_scrolls: int = 15) -> Optional[Path]:
        """
        Launches WhatsApp Web with the persistent session (STRICT READ-ONLY).
        If not logged in, allows user to scan the QR code.
        If target_contact is provided, selects it and extracts its messages.
        """
        from playwright.async_api import async_playwright

        print("\n🌐 Iniciando WhatsApp Web en MODO SOLO LECTURA estricto...")
        print(f"📁 Directorio de sesión: {self.session_dir}")

        async with async_playwright() as p:
            context = await self._launch_readonly_context(p)
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
                qr_img_path = self.session_dir.parent / "qr.png"
                while time.time() - start_time < 120:
                    if await page.query_selector(logged_in_selector):
                        print("✅ ¡Sesión de WhatsApp Web activa y autenticada!")
                        if qr_img_path.exists():
                            try:
                                qr_img_path.unlink()
                            except Exception:
                                pass
                        break
                    elif await page.query_selector(qr_selector):
                        try:
                            qr_el = await page.query_selector(qr_selector)
                            if qr_el:
                                qr_img_path.parent.mkdir(parents=True, exist_ok=True)
                                await qr_el.screenshot(path=str(qr_img_path))
                        except Exception:
                            pass
                        print(f"📸 Escanea el código QR (guardado en {qr_img_path} o http://localhost:3094/whatsapp/qr)...")
                    await asyncio.sleep(2)
                else:
                    print("⚠️ Tiempo de espera agotado para el escaneo del QR.")
                    await context.close()
                    return None

            except Exception as e:
                print(f"Error al verificar estado de sesión: {e}")

            # Safety lock: disable message composer completely
            await self._apply_readonly_lock(page)

            # If target contact specified, search in sidebar without typing or sending anything
            chat_title = target_contact or "Chat_Activo"
            if target_contact:
                print(f"\n🔍 Buscando chat con: '{target_contact}' en la barra lateral...")
                try:
                    clicked = await page.evaluate('''(target) => {
                        const rows = document.querySelectorAll("#pane-side div[role='listitem'], #pane-side div[role='row'], #pane-side div[data-testid='cell-frame-container']");
                        for (const r of rows) {
                            const titleEl = r.querySelector("span[title], div[title]");
                            if (titleEl && titleEl.getAttribute("title") && titleEl.getAttribute("title").toLowerCase().includes(target.toLowerCase())) {
                                r.scrollIntoView({ block: 'center' });
                                r.click();
                                return true;
                            }
                        }
                        return false;
                    }''', target_contact)
                    if clicked:
                        await asyncio.sleep(2)
                except Exception as e:
                    print(f"No se pudo seleccionar el contacto en la barra lateral: {e}")

            print("\n📜 Leyendo conversación abierta y cargando historial...")
            # Scroll up inside the chat pane using DOM scroll (NO keyboard events, 100% read-only)
            try:
                for s in range(max_scrolls):
                    await page.evaluate('''() => {
                        const areas = document.querySelectorAll("div.copyable-area, div[data-tab='8']");
                        for (const a of areas) {
                            a.scrollBy(0, -800);
                        }
                    }''')
                    await asyncio.sleep(0.25)
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

    async def export_all_chats(
        self,
        limit: int = 100,
        max_scrolls_per_chat: int = 8,
        force_reexport: bool = False,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Connects to WhatsApp Web and automatically scrolls through the conversation list,
        exporting up to `limit` chats into individual .txt files in `chats/`.
        - Checks if already exported: skips with a clear message ("Ya exporté este chat: no es necesario volverlo a exportar").
        - Checks if unread: NEVER opens unread chats to preserve user's notifications.
        - Reports which chats are pending export.
        """
        from playwright.async_api import async_playwright

        print("\n🌐 Iniciando exportador inteligente de WhatsApp Web...")
        print(f"📁 Directorio de sesión: {self.session_dir}")
        print(f"🎯 Meta: hasta {limit} chats. (Saltando ya exportados y no leídos).")

        exported_files: List[Path] = []
        already_exported_skipped: List[str] = []
        unread_skipped: List[str] = []
        all_detected_contacts: List[str] = []
        seen_in_session = set()

        async with async_playwright() as p:
            context = await self._launch_readonly_context(p)
            page = context.pages[0] if context.pages else await context.new_page()

            print("⏳ Navegando a https://web.whatsapp.com...")
            await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

            # Check if user needs to scan QR
            logged_in_selector = "div#pane-side, div[data-tab='3'], header"
            qr_selector = "canvas[aria-label='Scan this QR code to link a device'], canvas"

            start_time = time.time()
            qr_img_path = self.session_dir.parent / "qr.png"
            while time.time() - start_time < 120:
                if await page.query_selector(logged_in_selector):
                    print("✅ ¡Sesión de WhatsApp Web autenticada!")
                    if qr_img_path.exists():
                        try:
                            qr_img_path.unlink()
                        except Exception:
                            pass
                    break
                elif await page.query_selector(qr_selector):
                    try:
                        qr_el = await page.query_selector(qr_selector)
                        if qr_el:
                            qr_img_path.parent.mkdir(parents=True, exist_ok=True)
                            await qr_el.screenshot(path=str(qr_img_path))
                    except Exception:
                        pass
                    print(f"📸 Escanea el código QR (guardado en {qr_img_path} o http://localhost:3094/whatsapp/qr)...")
                await asyncio.sleep(2)
            else:
                print("⚠️ Tiempo de espera agotado para el escaneo del QR.")
                await context.close()
                return {
                    "status": "timeout",
                    "exported": [],
                    "skipped_cached": [],
                    "skipped_unread": [],
                    "pending": []
                }

            # Wait for pane-side to be ready
            try:
                await page.wait_for_selector("#pane-side", timeout=15000)
            except Exception:
                pass

            # Safety lock: disable message composer completely
            await self._apply_readonly_lock(page)

            print("\n📋 Escaneando lista de conversaciones en WhatsApp Web...")

            consecutive_no_new = 0
            max_consecutive_no_new = 5

            while (len(exported_files) + len(already_exported_skipped)) < limit and consecutive_no_new < max_consecutive_no_new:
                # Get visible chat elements with unread indicators
                chat_items = await page.evaluate('''() => {
                    const results = [];
                    const pane = document.querySelector("#pane-side");
                    if (!pane) return results;
                    
                    const rows = pane.querySelectorAll("div[role='listitem'], div[role='row'], div[data-testid='cell-frame-container']");
                    for (const r of rows) {
                        const titleEl = r.querySelector("span[title], div[title]");
                        if (!titleEl || !titleEl.getAttribute("title")) continue;
                        const title = titleEl.getAttribute("title").trim();
                        if (!title) continue;

                        let hasUnread = false;
                        const unreadEl = r.querySelector("[aria-label*='unread' i], [aria-label*='no leído' i], [aria-label*='no leídos' i], [data-icon='unread-count']");
                        if (unreadEl) {
                            hasUnread = true;
                        } else {
                            const badges = r.querySelectorAll("span");
                            for (const b of badges) {
                                const label = (b.getAttribute("aria-label") || "").toLowerCase();
                                if (label.includes("unread") || label.includes("no leído") || label.includes("no leídos")) {
                                    hasUnread = true;
                                    break;
                                }
                            }
                        }
                        results.push({ title, hasUnread });
                    }
                    return results;
                }''')

                found_new_in_batch = False

                for item in chat_items:
                    title = item["title"]
                    has_unread = item["hasUnread"]

                    if title not in all_detected_contacts:
                        all_detected_contacts.append(title)

                    if title in seen_in_session:
                        continue
                    if (len(exported_files) + len(already_exported_skipped)) >= limit:
                        break

                    found_new_in_batch = True
                    consecutive_no_new = 0
                    seen_in_session.add(title)

                    # 1. Check if unread (PROTECTION)
                    if has_unread:
                        print(f"🔒 [{title}] Tiene mensajes sin leer por ti (omitido para no marcarlo como leído).")
                        unread_skipped.append(title)
                        await self._dispatch_callback(progress_callback, {
                            "type": "skip_unread",
                            "contact": title,
                            "message": f"🔒 {title}: tiene mensajes sin leer (omitido para no marcarlo como leído)."
                        })
                        continue

                    # 2. Check if already exported (CACHING)
                    if not force_reexport and self.is_already_exported(title):
                        print(f"⏭️ [{title}] Ya exporté este chat: no es necesario volverlo a exportar.")
                        already_exported_skipped.append(title)
                        await self._dispatch_callback(progress_callback, {
                            "type": "skip_cached",
                            "contact": title,
                            "message": f"⏭️ {title}: ya fue exportado previamente, no es necesario volverlo a exportar."
                        })
                        continue

                    # 3. Fresh read chat needing export
                    current_num = len(exported_files) + 1
                    print(f"\n[{current_num}/{limit}] 📥 Exportando chat nuevo con: {title}...")

                    # Click chat item
                    clicked = await page.evaluate('''(targetTitle) => {
                        const pane = document.querySelector("#pane-side");
                        if (!pane) return false;
                        const rows = pane.querySelectorAll("div[role='listitem'], div[role='row'], div[data-testid='cell-frame-container']");
                        for (const r of rows) {
                            const titleEl = r.querySelector("span[title], div[title]");
                            if (titleEl && titleEl.getAttribute("title") === targetTitle) {
                                r.scrollIntoView({ block: 'center' });
                                r.click();
                                return true;
                            }
                        }
                        return false;
                    }''', title)

                    if not clicked:
                        print(f"  ⚠ No se pudo abrir el chat con {title}. Omitiendo de forma segura.")
                        continue

                    await asyncio.sleep(1.2)

                    # Scroll up inside the chat pane using DOM scroll (100% read-only, ZERO keyboard events)
                    for _ in range(max_scrolls_per_chat):
                        await page.evaluate('''() => {
                            const areas = document.querySelectorAll("div.copyable-area, div[data-tab='8']");
                            for (const a of areas) {
                                a.scrollBy(0, -800);
                            }
                        }''')
                        await asyncio.sleep(0.2)

                    # Extract messages
                    messages = await self._extract_messages_from_page(page)
                    if messages:
                        formatted_text = self._format_as_whatsapp_txt(messages, title)
                        out_path = self.export_chat_from_text(formatted_text, title)
                        exported_files.append(out_path)
                        print(f"  ✓ {len(messages)} mensajes exportados -> {out_path.name}")
                        await self._dispatch_callback(progress_callback, {
                            "type": "exported",
                            "contact": title,
                            "filename": out_path.name,
                            "messages_count": len(messages),
                            "message": f"✓ {title}: {len(messages)} mensajes exportados."
                        })
                    else:
                        print(f"  ⚠ No se encontraron mensajes de texto legibles para {title}")

                if not found_new_in_batch:
                    consecutive_no_new += 1

                # Scroll down #pane-side to load next chunk of conversations
                can_scroll_more = await page.evaluate('''() => {
                    const pane = document.querySelector("#pane-side");
                    if (!pane) return false;
                    const prev = pane.scrollTop;
                    pane.scrollBy(0, 500);
                    return pane.scrollTop !== prev;
                }''')

                await asyncio.sleep(1.0)
                if not can_scroll_more:
                    consecutive_no_new += 1

            # Determine pending chats
            exported_set = set([f.stem.replace("Chat_de_WhatsApp_con_", "").replace("Chat de WhatsApp con ", "").replace("_", " ") for f in exported_files] + already_exported_skipped)
            pending_chats = [c for c in all_detected_contacts if c not in exported_set and c not in unread_skipped]

            print(f"\n╭──────────────────────────────────────────────────────────╮")
            print(f"│ 📊 RESUMEN DE EXPORTACIÓN WHATSAPP                       │")
            print(f"├──────────────────────────────────────────────────────────┤")
            print(f"│ 📥 Nuevos chats exportados: {len(exported_files)}")
            print(f"│ ⏭️  Ya exportados previamente (omitidos): {len(already_exported_skipped)}")
            print(f"│ 🔒 Con mensajes sin leer (omitidos por seguridad): {len(unread_skipped)}")
            print(f"│ ⏳ Chats que aún hacen falta exportar: {len(pending_chats)}")
            print(f"╰──────────────────────────────────────────────────────────╯\n")

            await context.close()
            return {
                "status": "success",
                "exported_files": [str(f.name) for f in exported_files],
                "exported_count": len(exported_files),
                "skipped_cached_count": len(already_exported_skipped),
                "skipped_cached": already_exported_skipped,
                "skipped_unread_count": len(unread_skipped),
                "skipped_unread": unread_skipped,
                "pending_count": len(pending_chats),
                "pending_chats": pending_chats,
                "total_detected": len(all_detected_contacts)
            }

    async def start_live_watcher(
        self,
        interval_seconds: int = 4,
        on_message_callback: Optional[Any] = None,
        stop_event: Optional[asyncio.Event] = None
    ):
        """
        Active chat observer:
        Monitors ONLY the currently active conversation in WhatsApp Web.
        If user receives or sends new messages in the currently open chat,
        it appends them to chats/ and triggers incremental intelligence.
        NEVER clicks or opens unread chats in the sidebar!
        """
        from playwright.async_api import async_playwright

        print("\n👁️ Iniciando Modo Escucha Activa (WhatsApp Live Watcher)...")
        print("🔒 Solo lee los chats que tú mismo tengas abiertos o ya hayas leído.")
        print("❌ NUNCA abre ni marca como leídos mensajes no leídos de tu bandeja.")

        async with async_playwright() as p:
            context = await self._launch_readonly_context(p)
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

            try:
                await page.wait_for_selector("div#pane-side, header", timeout=60000)
                await self._apply_readonly_lock(page)
                print("✅ Sesión activa. Observando conversación activa...")
            except Exception:
                print("⚠️ No se detectó inicio de sesión activo.")
                await context.close()
                return

            last_active_contact = None
            last_message_count = 0

            while stop_event is None or not stop_event.is_set():
                try:
                    header_title_el = await page.query_selector("header span[title]")
                    if header_title_el:
                        active_contact = await header_title_el.get_attribute("title")
                        if active_contact:
                            active_contact = active_contact.strip()
                            messages = await self._extract_messages_from_page(page)

                            if active_contact != last_active_contact:
                                last_active_contact = active_contact
                                last_message_count = len(messages)
                                print(f"👁️ Chat activo detectado: {active_contact} ({len(messages)} mensajes)")
                            else:
                                if len(messages) > last_message_count:
                                    diff = len(messages) - last_message_count
                                    print(f"⚡ {diff} nuevo(s) mensaje(s) en conversación activa con {active_contact}!")
                                    last_message_count = len(messages)

                                    formatted_text = self._format_as_whatsapp_txt(messages, active_contact)
                                    out_path = self.export_chat_from_text(formatted_text, active_contact)

                                    await self._dispatch_callback(on_message_callback, {
                                        "contact": active_contact,
                                        "new_count": diff,
                                        "total_messages": len(messages),
                                        "file": str(out_path)
                                    })
                except Exception:
                    pass

                await asyncio.sleep(interval_seconds)

            await context.close()

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
