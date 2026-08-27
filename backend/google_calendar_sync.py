#!/usr/bin/env python3
"""
google_calendar_sync.py - Google Calendar & iCalendar Synchronization for WhatsApp Analyzer

Provides:
1. 1-Click Google Calendar web URL generator.
2. Standard RFC 5545 .ics (iCalendar) file generator.
3. Google Calendar API OAuth2 client for direct cloud synchronization.
4. Vault event updater for Obsidian CRM notes.
"""

import os
import re
import json
import logging
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger("google-calendar-sync")

# Storage directory for Google OAuth credentials and tokens
GOOGLE_DIR = Path.home() / ".ai_cli_google"
GOOGLE_DIR.mkdir(parents=True, exist_ok=True)
CREDENTIALS_FILE = GOOGLE_DIR / "credentials.json"
TOKEN_FILE = GOOGLE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def parse_flexible_datetime(dt_str: str, base_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parses flexible date/time strings into a datetime object.
    Supports ISO formats, natural formats (YYYY-MM-DD HH:MM), and relative times.
    """
    if not dt_str:
        return None

    dt_str = dt_str.strip()
    now = base_date or datetime.now()

    # Try ISO format
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        pass

    # Common date + time patterns
    patterns = [
        ("%Y-%m-%d %H:%M:%S", False),
        ("%Y-%m-%d %H:%M", False),
        ("%Y-%m-%d", True),
        ("%d/%m/%Y %H:%M", False),
        ("%d/%m/%Y", True),
        ("%H:%M", False)
    ]

    for fmt, is_date_only in patterns:
        try:
            parsed = datetime.strptime(dt_str, fmt)
            if fmt == "%H:%M":
                # Time today
                return now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
            if is_date_only:
                # Default to 19:00 (7 PM) for evening plans if no hour specified
                return parsed.replace(hour=19, minute=0, second=0, microsecond=0)
            return parsed
        except ValueError:
            continue

    # Relative patterns like "hoy a las 20:00", "mañana a las 15:00"
    dt_lower = dt_str.lower()
    time_match = re.search(r"(\d{1,2})[:.](\d{2})", dt_lower)
    hour = int(time_match.group(1)) if time_match else 19
    minute = int(time_match.group(2)) if time_match else 0

    if "hoy" in dt_lower:
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif "mañana" in dt_lower or "manana" in dt_lower:
        target = now + timedelta(days=1)
        return target.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif "pasado mañana" in dt_lower:
        target = now + timedelta(days=2)
        return target.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Days of week in Spanish
    weekdays = {
        "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2,
        "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6
    }
    for day_name, day_idx in weekdays.items():
        if day_name in dt_lower:
            days_ahead = (day_idx - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = now + timedelta(days=days_ahead)
            return target.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return None


def generate_google_calendar_url(
    title: str,
    start_dt: datetime,
    end_dt: Optional[datetime] = None,
    location: str = "",
    description: str = ""
) -> str:
    """
    Generates a 1-Click web link to prefill Google Calendar.
    Format: https://calendar.google.com/calendar/render?action=TEMPLATE&text=...
    """
    if not end_dt:
        end_dt = start_dt + timedelta(hours=2)

    # Google Calendar URL requires dates in YYYYMMDDTHHmmSS format
    dates_param = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": dates_param,
        "details": description,
        "location": location
    }

    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"


def generate_ics_file(
    title: str,
    start_dt: datetime,
    end_dt: Optional[datetime] = None,
    location: str = "",
    description: str = "",
    output_path: Optional[Path] = None
) -> Path:
    """
    Generates a standard .ics file using icalendar.
    """
    from icalendar import Calendar, Event

    if not end_dt:
        end_dt = start_dt + timedelta(hours=2)

    cal = Calendar()
    cal.add("prodid", "-//AI-CLI WhatsApp Analyzer//mx//")
    cal.add("version", "2.0")

    event = Event()
    event.add("summary", title)
    event.add("dtstart", start_dt)
    event.add("dtend", end_dt)
    event.add("dtstamp", datetime.now())
    if location:
        event.add("location", location)
    if description:
        event.add("description", description)

    cal.add_component(event)

    if not output_path:
        slug = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
        output_path = GOOGLE_DIR / f"{slug}.ics"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(cal.to_ical())

    return output_path


class GoogleCalendarSync:
    """
    Full Google Calendar API OAuth2 sync client.
    """

    def __init__(self, credentials_path: Optional[Path] = None):
        # Look in both ~/.ai_cli_google and ~/.ai_cli_whatsapp
        alt_cred = Path.home() / ".ai_cli_whatsapp" / "google_credentials.json"
        alt_tok = Path.home() / ".ai_cli_whatsapp" / "google_token.json"
        if credentials_path:
            self.credentials_path = Path(credentials_path)
        elif CREDENTIALS_FILE.exists():
            self.credentials_path = CREDENTIALS_FILE
        elif alt_cred.exists():
            self.credentials_path = alt_cred
        else:
            self.credentials_path = CREDENTIALS_FILE

        if TOKEN_FILE.exists():
            self.token_path = TOKEN_FILE
        elif alt_tok.exists():
            self.token_path = alt_tok
        else:
            self.token_path = TOKEN_FILE

        self.service = None

    def is_configured(self) -> bool:
        """Returns True if Google Calendar API credentials exist."""
        return self.credentials_path.exists() or self.token_path.exists()

    def get_status(self) -> Dict[str, Any]:
        """Returns structured status of Google Calendar integration."""
        is_configured = self.credentials_path.exists() or self.token_path.exists()
        is_authenticated = False

        if self.token_path.exists():
            try:
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
                if creds and (creds.valid or creds.refresh_token):
                    is_authenticated = True
            except Exception:
                pass

        return {
            "configured": is_configured,
            "authenticated": is_authenticated,
            "credentials_file": str(self.credentials_path),
            "credentials_exists": self.credentials_path.exists(),
            "token_file": str(self.token_path),
            "token_exists": self.token_path.exists(),
            "scopes": SCOPES
        }

    def get_auth_url(self, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Optional[str]:
        """Generates an OAuth authorization URL for the user."""
        if not self.credentials_path.exists():
            return None
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path),
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            return auth_url
        except Exception as e:
            logger.error(f"Error generando URL de OAuth: {e}")
            return None

    def complete_auth(self, code: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Dict[str, Any]:
        """Exchanges an authorization code for credentials and saves the token."""
        if not self.credentials_path.exists():
            return {"status": "error", "message": "credentials.json no existe."}
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path),
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            flow.fetch_token(code=code)
            creds = flow.credentials
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            self.service = None  # Reset cached service
            return {"status": "success", "message": "Autenticación completada con éxito."}
        except Exception as e:
            return {"status": "error", "message": f"Error al procesar el código: {e}"}

    def list_upcoming_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Returns upcoming events from the user's primary calendar."""
        service = self.get_service()
        if not service:
            return []
        try:
            now_iso = datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now_iso,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            items = events_result.get("items", [])
            output = []
            for item in items:
                start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                output.append({
                    "id": item.get("id"),
                    "summary": item.get("summary", "Sin título"),
                    "start": start,
                    "location": item.get("location", ""),
                    "html_link": item.get("htmlLink")
                })
            return output
        except Exception as e:
            logger.error(f"Error listando eventos: {e}")
            return []

    def get_service(self):
        """Builds and caches the Google Calendar API service instance."""
        if self.service:
            return self.service

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            logger.warning("google-api-python-client no está instalado en el entorno.")
            return None

        creds = None
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            except Exception as e:
                logger.warning(f"No se pudo cargar token existente: {e}")

        # Refresh or generate new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error al refrescar token de Google: {e}")
                    creds = None

            if not creds:
                if not self.credentials_path.exists():
                    logger.info(f"credentials.json no encontrado en {self.credentials_path}. La sincronización por API requiere este archivo.")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token for next time
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)
        return self.service

    def create_event(
        self,
        title: str,
        start_dt: Any,
        end_dt: Optional[Any] = None,
        location: str = "",
        description: str = "",
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Creates an event directly on the user's primary Google Calendar via API.
        Falls back to generating a 1-Click URL and an .ics file if API is not authenticated.
        """
        if isinstance(start_dt, str):
            start_dt = parse_flexible_datetime(start_dt) or datetime.now()
        if isinstance(end_dt, str):
            end_dt = parse_flexible_datetime(end_dt)

        if not end_dt:
            end_dt = start_dt + timedelta(hours=2)

        gcal_url = generate_google_calendar_url(title, start_dt, end_dt, location, description)
        ics_file = generate_ics_file(title, start_dt, end_dt, location, description)

        service = self.get_service()
        if not service:
            return {
                "status": "manual_ready",
                "google_calendar_url": gcal_url,
                "ics_path": str(ics_file),
                "message": "Credenciales API no activas. Usa el enlace 1-Click o el archivo .ics."
            }

        event_body = {
            "summary": title,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "America/Bogota"
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "America/Bogota"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "popup", "minutes": 15}
                ]
            }
        }

        if attendees:
            event_body["attendees"] = [{"displayName": a} for a in attendees if a]

        try:
            created_event = service.events().insert(calendarId="primary", body=event_body).execute()
            return {
                "status": "synced",
                "event_id": created_event.get("id"),
                "html_link": created_event.get("htmlLink"),
                "google_calendar_url": gcal_url,
                "ics_path": str(ics_file),
                "message": "¡Evento añadido exitosamente a Google Calendar!"
            }
        except Exception as e:
            logger.error(f"Error al insertar evento en Google Calendar: {e}")
            return {
                "status": "error",
                "error": str(e),
                "google_calendar_url": gcal_url,
                "ics_path": str(ics_file),
                "message": f"Fallo al sincronizar vía API: {e}. Usa el enlace 1-Click."
            }


calendar_sync = GoogleCalendarSync()
