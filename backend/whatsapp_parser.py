#!/usr/bin/env python3
"""
whatsapp_parser.py - WhatsApp Chat Export Parser and Relationship Analyzer
Parses WhatsApp exported chats (.txt) and extracts messages, timeline stats,
and prepares structured payloads for LLM entity/relationship extraction.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter


class WhatsAppParser:
    """Parser for exported WhatsApp chat transcripts."""

    # Regex patterns for different WhatsApp export formats:
    # 1. Android style: 15/01/24, 14:30 - John Doe: Hello there
    # 2. Android 12h: 1/15/24, 2:30 PM - John Doe: Hello
    # 3. iOS style: [15/01/24, 14:30:15] John Doe: Hello
    # 4. iOS 12h: [15/01/2024, 2:30:15 PM] John Doe: Hello
    PATTERNS = [
        # [DD/MM/YY(YY), HH:MM:SS (AM/PM)] Sender: Message
        re.compile(r"^\[(?P<date>\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{2,4}),?\s+(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\]\s+(?P<sender>[^:]+?):\s+(?P<message>.*)$"),
        # DD/MM/YY(YY), HH:MM (AM/PM) - Sender: Message
        re.compile(r"^(?P<date>\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{2,4}),?\s+(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\s+-\s+(?P<sender>[^:]+?):\s+(?P<message>.*)$"),
    ]

    SYSTEM_PATTERNS = [
        re.compile(r"cifrados de extremo a extremo|end-to-end encrypt|creó este grupo|añadió a|cambió el asunto|cambió el ícono|salió del grupo|eliminó a", re.IGNORECASE),
        re.compile(r"<Multimedia omitido>|<Media omitted>|archivo adjunto|omitted", re.IGNORECASE)
    ]

    def parse_text(self, text_content: str) -> Dict[str, Any]:
        """
        Parse raw WhatsApp chat text into structured messages and statistics.
        """
        lines = text_content.splitlines()
        messages: List[Dict[str, Any]] = []
        current_msg: Optional[Dict[str, Any]] = None

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            matched = False
            for pattern in self.PATTERNS:
                m = pattern.match(line_str)
                if m:
                    if current_msg:
                        messages.append(current_msg)

                    sender = m.group("sender").strip()
                    msg_text = m.group("message").strip()

                    # Check if it's a system message masquerading as a sender
                    is_system = any(sp.search(line_str) for sp in self.SYSTEM_PATTERNS)

                    current_msg = {
                        "date": m.group("date"),
                        "time": m.group("time"),
                        "sender": sender,
                        "message": msg_text,
                        "is_system": is_system
                    }
                    matched = True
                    break

            if not matched:
                if current_msg:
                    # Append multiline message content
                    current_msg["message"] += "\n" + line_str
                else:
                    # Header/system line before any message
                    pass

        if current_msg:
            messages.append(current_msg)

        # Generate Statistics
        total_messages = len(messages)
        user_messages = [m for m in messages if not m.get("is_system", False)]
        senders_counter = Counter(m["sender"] for m in user_messages)

        participants = []
        for sender, count in senders_counter.most_common():
            pct = round((count / max(1, len(user_messages))) * 100, 1)
            participants.append({
                "name": sender,
                "message_count": count,
                "percentage": pct
            })

        # Calculate word counts
        total_words = sum(len(m["message"].split()) for m in user_messages)

        # Media count
        media_count = sum(1 for m in messages if any(p.search(m["message"]) for p in self.SYSTEM_PATTERNS[1:]))

        return {
            "total_messages": total_messages,
            "user_messages_count": len(user_messages),
            "total_words": total_words,
            "media_count": media_count,
            "participants": participants,
            "messages": messages[:500],  # Keep reasonable chunk for preview
            "raw_messages_count": len(messages)
        }

    def build_analysis_prompt(self, parsed_data: Dict[str, Any], max_messages: int = 150) -> str:
        """
        Build an optimal LLM prompt to extract entities, relationships,
        birthdays, addresses, events, and generate contact summary notes.
        """
        participants = [p["name"] for p in parsed_data.get("participants", [])]
        messages = parsed_data.get("messages", [])

        # Filter and sample meaningful user messages
        user_msgs = [m for m in messages if not m.get("is_system", False)]
        sample = user_msgs[-max_messages:] if len(user_msgs) > max_messages else user_msgs

        formatted_chat = "\n".join([f"{m['sender']}: {m['message']}" for m in sample])

        prompt = f"""Analiza la siguiente conversación de WhatsApp entre los participantes: {', '.join(participants)}.

Extrae y organiza la información en formato JSON con la siguiente estructura:

```json
{{
  "resumen_general": "Resumen conciso del tipo de conversación, contexto y dinámica",
  "participantes": [
    {{
      "nombre": "Nombre del participante",
      "cumpleanos": "Fecha o 'No mencionado'",
      "direccion_ubicacion": "Dirección, ciudad o 'No mencionada'",
      "profesion_ocupacion": "Ocupación o 'No mencionada'",
      "intereses_hobbies": ["interés 1", "interés 2"],
      "notas_clave": ["Dato relevante 1", "Dato relevante 2"]
    }}
  ],
  "relacion": {{
    "tipo_vinculo": "Familiar / Amigos cercanos / Compañeros de trabajo / Pareja / etc.",
    "tono_conversacion": "Cálido / Informal / Profesional / etc.",
    "frecuencia_estimada": "Diaria / Semanal / Ocasional"
  }},
  "fechas_y_eventos_importantes": [
    {{
      "evento": "Descripción del evento o plan",
      "fecha": "Fecha o momento acordado"
    }}
  ],
  "acuerdos_o_tareas_pendientes": [
    "Compromiso 1",
    "Compromiso 2"
  ]
}}
```

CONVERSACIÓN:
{formatted_chat}

Responde ÚNICAMENTE con el objeto JSON estructurado, sin texto introductorio ni comentarios adicionales."""

        return prompt


# Singleton instance
whatsapp_parser = WhatsAppParser()
