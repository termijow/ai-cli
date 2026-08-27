#!/usr/bin/env python3
"""
obsidian_vault_exporter.py - WhatsApp Knowledge Base to Obsidian Vault CRM Exporter

Exports parsed WhatsApp conversations, contacts, profiles, key facts, and dates
into a structured Obsidian Vault with YAML Frontmatter, Dataview queries, Wikilinks,
and 1-Click Google Calendar / .ics event integrations.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

DEFAULT_VAULT_DIR = Path.home() / "Documents" / "Obsidian_WhatsApp_CRM"


class ObsidianVaultExporter:
    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_DIR
        self.contacts_dir = self.vault_path / "Contactos"
        self.conversations_dir = self.vault_path / "Conversaciones"
        self.events_dir = self.vault_path / "Eventos_y_Compromisos"
        self.places_dir = self.vault_path / "Lugares"
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [self.vault_path, self.contacts_dir, self.conversations_dir, self.events_dir, self.places_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _slugify(self, text: str) -> str:
        clean = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE).strip()
        return re.sub(r'[-\s]+', '_', clean)

    def read_contact_memory(self, contact_name: str) -> Optional[Dict[str, Any]]:
        """
        Reads existing knowledge about a contact from the Obsidian Vault.
        Parses YAML frontmatter and notes to provide prior context to Qwen 3.6.
        """
        self._ensure_dirs()
        slug = self._slugify(contact_name)
        target_path = self.contacts_dir / f"{slug}.md"

        if not target_path.exists():
            # Search case-insensitively or fuzzy
            for f in self.contacts_dir.glob("*.md"):
                if contact_name.lower() in f.stem.lower() or f.stem.lower() in contact_name.lower():
                    target_path = f
                    break

        if not target_path.exists():
            return None

        try:
            content = target_path.read_text(encoding="utf-8")
            memory = {
                "nombre": contact_name,
                "cumpleanos": None,
                "direccion_ubicacion": None,
                "profesion_ocupacion": None,
                "intereses_hobbies": [],
                "notas_previas": []
            }

            # Parse YAML Frontmatter
            fm_match = re.search(r"^---\s*\n(.*?)\n---", content, flags=re.DOTALL)
            if fm_match:
                fm_text = fm_match.group(1)
                for line in fm_text.splitlines():
                    if line.startswith("cumpleanos:"):
                        val = line.split(":", 1)[1].strip().strip('"\'')
                        if val and val != "None":
                            memory["cumpleanos"] = val
                    elif line.startswith("ubicacion:"):
                        val = line.split(":", 1)[1].strip().strip('"\'')
                        if val and val != "None":
                            memory["direccion_ubicacion"] = val
                    elif line.startswith("profesion:"):
                        val = line.split(":", 1)[1].strip().strip('"\'')
                        if val and val != "None":
                            memory["profesion_ocupacion"] = val
                    elif line.startswith("intereses:"):
                        try:
                            val = line.split(":", 1)[1].strip()
                            memory["intereses_hobbies"] = json.loads(val)
                        except Exception:
                            pass

            # Parse Notes
            notes_match = re.search(r"## 📝 Historial de Hechos, Anécdotas y Notas Clave\s*\n(.*?)(?=\n## |\Z)", content, flags=re.DOTALL)
            if notes_match:
                for line in notes_match.group(1).splitlines():
                    line = line.strip()
                    if line.startswith("- 🔹") or line.startswith("-"):
                        clean_note = re.sub(r"^-\s*🔹?\s*", "", line)
                        if clean_note and not clean_note.startswith("*Sin notas"):
                            memory["notas_previas"].append(clean_note)

            return memory
        except Exception as e:
            print(f"Error leyendo memoria de contacto en Obsidian: {e}")
            return None

    def export_event_note(self, event: Dict[str, Any], contact_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates an individual markdown note and .ics file in Eventos_y_Compromisos/
        with 1-Click Google Calendar URL and metadata.
        """
        from backend.google_calendar_sync import (
            parse_flexible_datetime,
            generate_google_calendar_url,
            generate_ics_file
        )

        title = event.get("titulo") or event.get("descripcion") or "Compromiso de WhatsApp"
        location = event.get("lugar") or ""
        date_str = str(event.get("fecha") or event.get("fecha_inicio") or "")
        desc = event.get("descripcion") or f"Plan acordado con {contact_name or 'contacto'}"

        now = datetime.now()
        start_dt = parse_flexible_datetime(date_str) or (now + timedelta(days=1)).replace(hour=20, minute=0, second=0)
        end_dt = start_dt + timedelta(hours=2)

        gcal_url = generate_google_calendar_url(title, start_dt, end_dt, location, desc)

        slug = self._slugify(f"{start_dt.strftime('%Y%m%d')}_{title}")
        event_path = self.events_dir / f"{slug}.md"
        ics_path = self.events_dir / f"{slug}.ics"

        # Generate .ics file
        try:
            generate_ics_file(title, start_dt, end_dt, location, desc, output_path=ics_path)
        except Exception as e:
            print(f"Nota: No se pudo generar .ics: {e}")

        contact_wikilink = f"[[{contact_name}]]" if contact_name else "[[Contacto]]"
        loc_wikilink = f"[[{location}]]" if location else "*No especificado*"

        frontmatter = [
            "---",
            f"id: evento-{slug}",
            f"titulo: \"{title}\"",
            "tags: [evento, compromiso, whatsapp, calendario]",
            f"fecha: \"{start_dt.strftime('%Y-%m-%d')}\"",
            f"hora: \"{start_dt.strftime('%H:%M')}\"",
            f"lugar: \"{location}\"",
            f"contacto: \"{contact_wikilink}\"",
            "google_calendar_status: \"pendiente\"",
            f"google_calendar_url: \"{gcal_url}\"",
            f"ics_file: \"{ics_path.name}\"",
            f"fecha_deteccion: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
            "---"
        ]

        body = [
            f"# 📅 {title}",
            "",
            "## 📌 Detalles del Evento / Compromiso",
            f"- **📆 Fecha:** {start_dt.strftime('%A, %d de %B de %Y')}",
            f"- **⏰ Hora:** {start_dt.strftime('%H:%M')}",
            f"- **📍 Lugar:** {loc_wikilink}",
            f"- **👥 Participantes:** {contact_wikilink}",
            "",
            "## 📝 Contexto del Acuerdo",
            f"> {desc}",
            "",
            "## 🌐 Sincronización de Calendario",
            f"- 🔗 **[👉 Añadir a Google Calendar (1 Clic Web)]({gcal_url})**",
            f"- 📥 **Archivo Calendario Local (.ics):** `[[{ics_path.name}]]` *(haz doble clic para agregarlo a tu calendario del sistema)*",
            ""
        ]

        event_path.write_text("\n".join(frontmatter) + "\n\n" + "\n".join(body), encoding="utf-8")
        return {
            "title": title,
            "path": str(event_path),
            "ics_path": str(ics_path),
            "google_calendar_url": gcal_url,
            "start_dt": start_dt.isoformat()
        }

    def export_profile(self, profile: Dict[str, Any], chat_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export full WhatsApp profile and contacts to Obsidian Vault."""
        self._ensure_dirs()
        exported_contacts = []
        exported_events = 0

        participants = profile.get("participantes", [])
        events = profile.get("eventos_y_compromisos", [])

        # 1. Export each Contact Note
        for p in participants:
            name = p.get("nombre") or "Contacto_Sin_Nombre"
            filename = f"{self._slugify(name)}.md"
            contact_path = self.contacts_dir / filename

            # Build Wikilinks for places and professions
            location = p.get("direccion_ubicacion") or ""
            profession = p.get("profesion_ocupacion") or ""
            birthday = p.get("cumpleanos") or ""
            hobbies = p.get("intereses_hobbies") or []
            notes = p.get("notas_clave") or []

            # Save Place note if location exists
            if location and location.lower() != "no mencionada":
                loc_slug = self._slugify(location)
                loc_path = self.places_dir / f"{loc_slug}.md"
                if not loc_path.exists():
                    loc_content = f"---\ntags: [lugar, ubicacion]\n---\n# 📍 {location}\n\nLugar mencionado en conversaciones de WhatsApp.\n\n## Contactos Relacionados\n```dataview\nLIST FROM #contacto WHERE contains(ubicacion, \"{location}\")\n```\n"
                    loc_path.write_text(loc_content, encoding="utf-8")

            # Frontmatter YAML for Obsidian Dataview
            frontmatter = [
                "---",
                f"id: contacto-{self._slugify(name).lower()}",
                f"nombre: \"{name}\"",
                f"aliases: [\"{name}\"]",
                "tags: [contacto, whatsapp, crm, inteligencia_personal]",
                f"cumpleanos: \"{birthday}\"",
                f"ubicacion: \"{location}\"",
                f"profesion: \"{profession}\"",
                f"intereses: {json.dumps(hobbies, ensure_ascii=False)}",
                f"total_notas: {len(notes)}",
                f"fecha_actualizacion: \"{datetime.now().strftime('%Y-%m-%d %H:%M')}\"",
                "---"
            ]

            body = [
                f"# 👤 {name}",
                "",
                "## 📌 Ficha de Perfil Rápido",
                f"- **🎂 Cumpleaños:** {f'[[{birthday}]]' if birthday else '*No mencionado*'}",
                f"- **📍 Ubicación / Dirección:** {f'[[{location}]]' if location and location != 'No mencionada' else '*No mencionada*'}",
                f"- **💼 Profesión / Estudios:** {f'[[{profession}]]' if profession and profession != 'No mencionada' else '*No mencionada*'}",
                f"- **❤️ Intereses y Hobbies:** {', '.join([f'#{self._slugify(h)}' for h in hobbies]) if hobbies else '*Ninguno registrado*'}",
                "",
                "## 📝 Historial de Hechos, Anécdotas y Notas Clave",
            ]

            if notes:
                for note in notes:
                    body.append(f"- 🔹 {note}")
            else:
                body.append("- *Sin notas específicas registradas.*")

            body.extend([
                "",
                "## 📅 Planes y Eventos Agendados",
                "```dataview",
                f'TABLE fecha as "📆 Fecha", hora as "⏰ Hora", lugar as "📍 Lugar", google_calendar_status as "Google Status"',
                f'FROM #evento WHERE contains(contacto, "[[{name}]]")',
                f'SORT fecha ASC',
                "```",
                "",
                "## 🤝 Compromisos y Tareas Pendientes",
                "```dataview",
                f'TASK FROM #compromiso WHERE contains(text, "{name}")',
                "```",
                "",
                "## 🔗 Relaciones y Menciones",
                "```dataview",
                f'LIST FROM #whatsapp WHERE contains(file.outlinks, [[{name}]])',
                "```",
                ""
            ])

            full_content = "\n".join(frontmatter) + "\n\n" + "\n".join(body)
            contact_path.write_text(full_content, encoding="utf-8")
            exported_contacts.append(name)

        # 2. Export Individual Event Notes with 1-Click Google Calendar links
        if events:
            for ev in events:
                try:
                    c_name = participants[0].get("nombre") if participants else None
                    self.export_event_note(ev, contact_name=c_name)
                    exported_events += 1
                except Exception as e:
                    print(f"Error al exportar nota de evento: {e}")

            # Also maintain global agenda file
            events_file = self.events_dir / "Compromisos_y_Eventos.md"
            events_lines = [
                "---",
                "tags: [eventos, compromisos, agenda, whatsapp]",
                f"fecha_actualizacion: \"{datetime.now().strftime('%Y-%m-%d')}\"",
                "---",
                "# 📅 Agenda de Eventos y Compromisos de WhatsApp",
                "",
                "Lista de fechas importantes, reuniones y acuerdos extraídos por la IA.",
                ""
            ]
            for ev in events:
                fecha = ev.get("fecha") or "Fecha sin especificar"
                desc = ev.get("descripcion") or ""
                events_lines.append(f"- [ ] **[[{fecha}]]:** {desc} #compromiso")

            events_file.write_text("\n".join(events_lines), encoding="utf-8")

        # 3. Create or update Master Dashboard / CRM Hub
        self._update_master_dashboard()

        return {
            "success": True,
            "vault_path": str(self.vault_path),
            "contacts_exported": exported_contacts,
            "total_contacts": len(exported_contacts),
            "events_exported": exported_events
        }

    def _update_master_dashboard(self):
        """Generates the master Dashboard_CRM.md file in the Obsidian vault."""
        dashboard_path = self.vault_path / "📊_Dashboard_CRM.md"
        content = """---
tags: [dashboard, crm, whatsapp_hub]
---

# 🧠 WhatsApp Intelligence CRM & Contact Hub

> [!NOTE]
> Base de datos de relaciones personales y compromisos sincronizada automáticamente con **AI-CLI Studio** y **Qwen 3.6 35B A3B**.

## 👥 Directorio de Contactos
```dataview
TABLE 
    cumpleanos as "🎂 Cumpleaños", 
    ubicacion as "📍 Ubicación / Dirección", 
    profesion as "💼 Profesión", 
    total_notas as "📝 Notas"
FROM #contacto
SORT file.name ASC
```

---

## 📅 Próximos Eventos y Salidas
```dataview
TABLE 
    fecha as "📆 Fecha", 
    hora as "⏰ Hora", 
    contacto as "👥 Con Quién", 
    lugar as "📍 Lugar", 
    google_calendar_status as "Google Calendar"
FROM #evento
SORT fecha ASC
```

---

## 🤝 Tareas y Acuerdos Pendientes
```dataview
TASK
FROM #compromiso
WHERE !completed
```

---

## 🗺️ Lugares y Ciudades Registradas
```dataview
LIST
FROM #lugar
```
"""
        dashboard_path.write_text(content, encoding="utf-8")

    def get_status(self) -> Dict[str, Any]:
        """Returns statistics of the current Obsidian Vault."""
        if not self.vault_path.exists():
            return {"exists": False, "vault_path": str(self.vault_path), "contacts": 0}

        contacts = list(self.contacts_dir.glob("*.md")) if self.contacts_dir.exists() else []
        events = list(self.events_dir.glob("*.md")) if self.events_dir.exists() else []
        return {
            "exists": True,
            "vault_path": str(self.vault_path),
            "contacts_count": len(contacts),
            "contacts": [c.stem for c in contacts],
            "events_count": len(events)
        }


vault_exporter = ObsidianVaultExporter()
