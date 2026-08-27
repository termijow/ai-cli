#!/usr/bin/env python3
"""
whatsapp_analyzer_engine.py - Chunking & Incremental Map-Reduce Note-Taking Engine
Handles massive WhatsApp chats (from 10K to 1M+ tokens) by chunking them chronologically,
running batch-by-batch entity & relationship extraction with the local LLM, and synthesizing
an evolving contact profile and dossier with real-time progress events.
"""

import os
import sys
import json
import re
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator, Callable
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.whatsapp_parser import WhatsAppParser, whatsapp_parser
from backend.obsidian_vault_exporter import vault_exporter

STORAGE_DIR = Path.home() / ".ai_cli_whatsapp"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def extract_json_from_llm(text: str) -> Optional[Dict[str, Any]]:
    """Robustly extract JSON object from LLM response, stripping think tags and markdown."""
    if not text:
        return None

    # 1. Strip think blocks if present
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL).strip()
    if not cleaned:
        cleaned = text

    # 2. Try markdown json block
    matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    for m in reversed(matches):
        try:
            return json.loads(m.strip())
        except Exception:
            pass

    # 3. Try finding largest JSON object { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(cleaned[first_brace:last_brace + 1])
        except Exception:
            pass

    # 4. Fallback: try raw text
    try:
        return json.loads(text.strip())
    except Exception:
        return None


class LargeChatAnalyzer:
    """
    Engine that parses, chunks, and incrementally analyzes massive WhatsApp chat transcripts.
    """

    def __init__(self, chunk_size_messages: int = 150):
        self.chunk_size = chunk_size_messages
        self.parser = WhatsAppParser()

    def parse_and_chunk(self, raw_chat_text: str) -> Dict[str, Any]:
        """
        Parse raw chat text and divide messages into chronological chunks.
        """
        parsed_stats = self.parser.parse_text(raw_chat_text)
        user_messages = [m for m in parsed_stats.get("messages", []) if not m.get("is_system", False)]

        # If user_messages only contains preview messages, re-extract all from raw_chat_text
        all_lines = raw_chat_text.splitlines()
        all_messages: List[Dict[str, Any]] = []
        curr = None

        for line in all_lines:
            line_str = line.strip()
            if not line_str:
                continue

            matched = False
            for pattern in self.parser.PATTERNS:
                m = pattern.match(line_str)
                if m:
                    if curr:
                        all_messages.append(curr)
                    sender = m.group("sender").strip()
                    is_system = any(sp.search(line_str) for sp in self.parser.SYSTEM_PATTERNS)
                    curr = {
                        "date": m.group("date"),
                        "time": m.group("time"),
                        "sender": sender,
                        "message": m.group("message").strip(),
                        "is_system": is_system
                    }
                    matched = True
                    break

            if not matched and curr:
                curr["message"] += "\n" + line_str

        if curr:
            all_messages.append(curr)

        all_user_messages = [m for m in all_messages if not m.get("is_system", False)]
        if not all_user_messages:
            all_user_messages = all_messages

        # Create batches
        chunks = []
        for i in range(0, len(all_user_messages), self.chunk_size):
            chunk_slice = all_user_messages[i:i + self.chunk_size]
            date_start = chunk_slice[0]["date"] if chunk_slice else "N/A"
            date_end = chunk_slice[-1]["date"] if chunk_slice else "N/A"
            chunks.append({
                "index": len(chunks) + 1,
                "date_range": f"{date_start} - {date_end}" if date_start != date_end else date_start,
                "messages": chunk_slice,
                "message_count": len(chunk_slice)
            })

        # Top participants
        participants_counter = Counter(m["sender"] for m in all_user_messages)
        total_user_msgs = len(all_user_messages)
        participants = [
            {"name": k, "message_count": v, "percentage": round((v / max(1, total_user_msgs)) * 100, 1)}
            for k, v in participants_counter.most_common(10)
        ]

        return {
            "total_messages": len(all_messages),
            "total_user_messages": total_user_msgs,
            "total_words": sum(len(m["message"].split()) for m in all_user_messages),
            "participants": participants,
            "total_chunks": len(chunks),
            "chunks": chunks
        }

    def create_batch_prompt(
        self,
        chunk: Dict[str, Any],
        accumulated_summary: Dict[str, Any],
        participants: List[str]
    ) -> str:
        """
        Build an incremental extraction prompt for this specific chunk.
        """
        dialogue = "\n".join([f"{m['sender']}: {m['message']}" for m in chunk["messages"]])
        known_context = json.dumps(accumulated_summary.get("participantes", []), ensure_ascii=False, indent=2)

        prompt = f"""Estás analizando un fragmento cronológico ({chunk['date_range']}) de una conversación de WhatsApp entre: {', '.join(participants)}.

DATOS YA CONOCIDOS DE LOS PARTICIPANTES (MEMORIA PREVIA OBSIDIAN CRM):
{known_context}

NUEVO FRAGMENTO DE CHAT ({chunk['message_count']} mensajes):
{dialogue}

TAREA DE EXTRACCIÓN CON MODELO LOCAL QWEN 3.6:
Extrae hechos nuevos, detalles concretos o actualizaciones mencionadas en este fragmento.
Enfócate en:
1. Datos Personales Concretos: Cumpleaños, edad, dirección donde vive o trabaja, ciudad, profesión, gustos, comidas favoritas, hobbies.
2. CITAS, SALIDAS Y EVENTOS (CRUCIAL PARA GOOGLE CALENDAR):
   Si en la conversación acuerdan salir, verse, una reunión o plan (ej: "salimos?", "vamos a Xx a las XX", "nos vemos mañana a las 3"), extrae el evento con su título, fecha y hora estimada, y lugar exacto.

IMPORTANTE: Sé directo y genera el bloque JSON válido inmediatamente sin razonamientos extensos.

Responde en JSON con este formato:
```json
{{
  "nuevas_notas_participantes": [
    {{
      "nombre": "Nombre del participante",
      "cumpleanos": "Fecha o edad o null",
      "direccion_o_ciudad": "Dirección exacta, barrio o ciudad o null",
      "profesion_o_estudios": "Profesión, estudios o null",
      "gustos_e_intereses": ["interés o comida o hobby nuevo"],
      "hechos_clave": ["Hecho o anécdota relevante"]
    }}
  ],
  "eventos_o_acuerdos": [
    {{
      "titulo": "Título descriptivo de la salida (ej: Salida con Felipe a Xx)",
      "fecha": "Fecha y hora del plan (ej: 2026-08-28 20:00 o hoy a las 8pm)",
      "lugar": "Lugar exacto del encuentro o null",
      "descripcion": "Detalle del plan o salida acordada",
      "es_salida_o_cita": true
    }}
  ],
  "resumen_fragmento": "Resumen de 1 o 2 oraciones de lo que hablaron en esta etapa"
}}
```"""
        return prompt

    def merge_batch_delta(self, global_profile: Dict[str, Any], batch_delta: Dict[str, Any], date_range: str):
        """
        Merge extracted delta facts into the cumulative global profile.
        """
        if not isinstance(batch_delta, dict):
            return

        # Merge participant notes
        known_parts = {p["nombre"].lower(): p for p in global_profile.setdefault("participantes", [])}

        for new_p in batch_delta.get("nuevas_notas_participantes", []):
            if not isinstance(new_p, dict) or not new_p.get("nombre"):
                continue

            name = new_p["nombre"].strip()
            name_key = name.lower()

            if name_key not in known_parts:
                known_parts[name_key] = {
                    "nombre": name,
                    "cumpleanos": None,
                    "direccion_ubicacion": None,
                    "profesion_ocupacion": None,
                    "intereses_hobbies": [],
                    "notas_clave": []
                }
                global_profile["participantes"].append(known_parts[name_key])

            target = known_parts[name_key]

            # Update fields if found
            if new_p.get("cumpleanos") and not target.get("cumpleanos"):
                target["cumpleanos"] = new_p["cumpleanos"]

            if new_p.get("direccion_o_ciudad") and not target.get("direccion_ubicacion"):
                target["direccion_ubicacion"] = new_p["direccion_o_ciudad"]

            if new_p.get("profesion_o_estudios") and not target.get("profesion_ocupacion"):
                target["profesion_ocupacion"] = new_p["profesion_o_estudios"]

            for hobby in new_p.get("gustos_e_intereses", []):
                if hobby and hobby not in target["intereses_hobbies"]:
                    target["intereses_hobbies"].append(hobby)

            for fact in new_p.get("hechos_clave", []):
                fact_entry = f"[{date_range}] {fact}"
                if fact and fact_entry not in target["notas_clave"]:
                    target["notas_clave"].append(fact_entry)

        # Merge events and plans
        events_list = global_profile.setdefault("eventos_y_compromisos", [])
        for ev in batch_delta.get("eventos_o_acuerdos", []):
            if isinstance(ev, dict) and (ev.get("descripcion") or ev.get("titulo")):
                title = ev.get("titulo") or ev.get("descripcion", "Plan acordado")
                events_list.append({
                    "titulo": title,
                    "fecha": ev.get("fecha") or date_range,
                    "lugar": ev.get("lugar") or "",
                    "descripcion": ev.get("descripcion") or title,
                    "es_salida_o_cita": ev.get("es_salida_o_cita", True)
                })

        # Append timeline stage summary
        stage_summary = batch_delta.get("resumen_fragmento")
        if stage_summary:
            global_profile.setdefault("cronologia_resumenes", []).append({
                "etapa": date_range,
                "resumen": stage_summary
            })

    async def analyze_chat_stream(
        self,
        raw_chat_text: str,
        query_llm_fn: Callable[[str], Dict[str, Any]],
        chat_title: str = "WhatsApp_Chat"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator that yields real-time progress events for each batch processed.
        """
        yield {
            "type": "status",
            "message": "Analizando estructura y dividiendo conversación en fragmentos...",
            "percent": 5
        }

        chunk_data = self.parse_and_chunk(raw_chat_text)
        total_chunks = chunk_data["total_chunks"]
        chunks = chunk_data["chunks"]
        participants = [p["name"] for p in chunk_data["participants"]]

        if total_chunks == 0:
            yield {
                "type": "error",
                "message": "No se encontraron mensajes válidos para analizar en el chat."
            }
            return

        yield {
            "type": "init",
            "total_messages": chunk_data["total_messages"],
            "total_words": chunk_data["total_words"],
            "total_chunks": total_chunks,
            "participants": chunk_data["participants"],
            "chat_title": chat_title,
            "percent": 10
        }

        # 1. Cargar memoria previa conocida del contacto desde Obsidian CRM
        prior_memory = vault_exporter.read_contact_memory(chat_title)
        initial_participants = []
        if prior_memory:
            initial_participants.append({
                "nombre": prior_memory["nombre"],
                "cumpleanos": prior_memory.get("cumpleanos"),
                "direccion_ubicacion": prior_memory.get("direccion_ubicacion"),
                "profesion_ocupacion": prior_memory.get("profesion_ocupacion"),
                "intereses_hobbies": prior_memory.get("intereses_hobbies") or [],
                "notas_clave": prior_memory.get("notas_previas") or []
            })

        global_profile: Dict[str, Any] = {
            "titulo": chat_title,
            "total_mensajes": chunk_data["total_messages"],
            "participantes": initial_participants,
            "eventos_y_compromisos": [],
            "cronologia_resumenes": [],
            "total_batches_procesados": 0
        }

        total_tokens_spent = 0

        # Process batch by batch
        for idx, chunk in enumerate(chunks, 1):
            percent = int(10 + ((idx - 1) / total_chunks) * 80)
            yield {
                "type": "batch_start",
                "batch_index": idx,
                "total_batches": total_chunks,
                "date_range": chunk["date_range"],
                "message_count": chunk["message_count"],
                "percent": percent,
                "message": f"Procesando fragmento {idx}/{total_chunks} ({chunk['date_range']})..."
            }

            prompt = self.create_batch_prompt(chunk, global_profile, participants)

            # Call LLM
            loop = asyncio.get_event_loop()
            llm_result = await loop.run_in_executor(None, query_llm_fn, prompt)

            content = llm_result.get("content", "")
            tokens_used = llm_result.get("tokens_used", 0)
            total_tokens_spent += tokens_used

            # Parse JSON delta from LLM response
            delta_json = extract_json_from_llm(content)

            if delta_json:
                self.merge_batch_delta(global_profile, delta_json, chunk["date_range"])

            global_profile["total_batches_procesados"] = idx

            # Yield batch completion update with current snapshot
            yield {
                "type": "batch_complete",
                "batch_index": idx,
                "total_batches": total_chunks,
                "date_range": chunk["date_range"],
                "percent": int(10 + (idx / total_chunks) * 80),
                "tokens_used": tokens_used,
                "total_tokens": total_tokens_spent,
                "current_profile": global_profile,
                "delta": delta_json
            }

        # Final Synthesis
        yield {
            "type": "status",
            "message": "Sintetizando dossier final y guardando resultados...",
            "percent": 95
        }

        # Save to local storage
        slug = re.sub(r"[^\w\-_]", "_", chat_title).lower()
        save_path_json = STORAGE_DIR / f"{slug}_profile.json"
        save_path_md = STORAGE_DIR / f"{slug}_dossier.md"

        with open(save_path_json, "w", encoding="utf-8") as f:
            json.dump(global_profile, f, ensure_ascii=False, indent=2)

        markdown_dossier = self.generate_markdown_dossier(global_profile, chunk_data)
        with open(save_path_md, "w", encoding="utf-8") as f:
            f.write(markdown_dossier)

        # 2. Sincronización y exportación automática a Obsidian CRM y Google Calendar
        try:
            obsidian_result = vault_exporter.export_profile(global_profile)
        except Exception as e:
            obsidian_result = {"error": str(e)}

        yield {
            "type": "complete",
            "percent": 100,
            "message": "¡Análisis completado con éxito! Libreta de Obsidian y eventos actualizados.",
            "profile": global_profile,
            "markdown_dossier": markdown_dossier,
            "saved_json": str(save_path_json),
            "saved_md": str(save_path_md),
            "obsidian_crm": obsidian_result,
            "total_tokens_spent": total_tokens_spent
        }

    def generate_markdown_dossier(self, profile: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """Create a polished Markdown dossier summarizing all accumulated intelligence."""
        md = []
        md.append(f"# 🗂️ Dossier de Relación e Inteligencia de Contactos")
        md.append(f"**Conversación:** {profile.get('titulo', 'WhatsApp Chat')}")
        md.append(f"**Fecha de Análisis:** {time.strftime('%Y-%m-%d %H:%M')}")
        md.append(f"**Mensajes Analizados:** {stats.get('total_messages', 0):,} ({stats.get('total_words', 0):,} palabras)")
        md.append(f"**Fragmentos Procesados:** {profile.get('total_batches_procesados', 0)}")
        md.append("\n---\n")

        md.append("## 👥 Perfiles de Participantes Extraídos")
        for p in profile.get("participantes", []):
            md.append(f"### 👤 {p.get('nombre', 'Contacto')}")
            md.append(f"- 🎂 **Cumpleaños:** {p.get('cumpleanos') or 'No mencionado'}")
            md.append(f"- 📍 **Ubicación / Dirección:** {p.get('direccion_ubicacion') or 'No mencionada'}")
            md.append(f"- 💼 **Profesión / Estudios:** {p.get('profesion_ocupacion') or 'No mencionada'}")

            hobbies = p.get("intereses_hobbies", [])
            if hobbies:
                md.append(f"- 🎯 **Gustos e Intereses:** {', '.join(hobbies)}")

            notes = p.get("notas_clave", [])
            if notes:
                md.append(f"- 📝 **Historial de Hechos y Anécdotas:**")
                for n in notes:
                    md.append(f"  • {n}")
            md.append("")

        events = profile.get("eventos_y_compromisos", [])
        if events:
            md.append("## 📅 Cronograma de Eventos, Planes y Compromisos")
            for ev in events:
                md.append(f"- **[{ev.get('fecha', 'Fecha')}]:** {ev.get('descripcion')}")
            md.append("")

        stages = profile.get("cronologia_resumenes", [])
        if stages:
            md.append("## 📜 Evolución y Resumen Cronológico de la Conversación")
            for st in stages:
                md.append(f"#### 🗓️ Etapa: {st.get('etapa')}")
                md.append(f"{st.get('resumen')}\n")

        md.append("\n---\n*Generado 100% en local por AI-CLI (Qwen LLM)*\n")
        return "\n".join(md)


# Global instance
analyzer_engine = LargeChatAnalyzer()
