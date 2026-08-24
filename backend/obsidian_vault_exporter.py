#!/usr/bin/env python3
"""
obsidian_vault_exporter.py - WhatsApp Knowledge Base to Obsidian Vault CRM Exporter

Exports parsed WhatsApp conversations, contacts, profiles, key facts, and dates
into a structured Obsidian Vault with YAML Frontmatter, Dataview queries, and Wikilinks.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

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

    def export_profile(self, profile: Dict[str, Any], chat_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export full WhatsApp profile and contacts to Obsidian Vault."""
        self._ensure_dirs()
        exported_contacts = []
        exported_events = 0

        participants = profile.get("participantes", [])
        events = profile.get("eventos_y_compromisos", [])
        chronology = profile.get("cronologia_resumenes", [])

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
                f"- **📍 Ubicación:** {f'[[{location}]]' if location and location != 'No mencionada' else '*No mencionada*'}",
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

        # 2. Export Global Events and Commitments
        if events:
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
                exported_events += 1

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
> Base de datos de relaciones personales y compromisos sincronizada automáticamente con **AI-CLI Studio**.

## 👥 Directorio de Contactos
```dataview
TABLE 
    cumpleanos as "🎂 Cumpleaños", 
    ubicacion as "📍 Ubicación", 
    profesion as "💼 Profesión", 
    total_notas as "📝 Notas"
FROM #contacto
SORT file.name ASC
```

---

## 📅 Próximos Eventos y Tareas Pendientes
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
        return {
            "exists": True,
            "vault_path": str(self.vault_path),
            "contacts_count": len(contacts),
            "contacts": [c.stem for c in contacts]
        }

vault_exporter = ObsidianVaultExporter()
