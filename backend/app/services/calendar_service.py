from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.calendar import CalendarEvent
from app.models.user import User

class CalendarService:
    @staticmethod
    def get_events_for_range(
        db: Session,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> List[CalendarEvent]:
        start_dt = datetime.combine(start_date, time(0, 0, 0))
        end_dt = datetime.combine(end_date, time(23, 59, 59))
        
        return db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_dt,
            CalendarEvent.start_time <= end_dt
        ).order_by(CalendarEvent.start_time.asc()).all()

    @staticmethod
    def seed_demo_calendar(db: Session, user_id: str):
        """
        Seeds a realistic 7-day calendar with a mix of heavy meeting days (Orange/Red)
        and light focus days (Green/Yellow) to demonstrate smart scheduling.
        """
        # Clear existing demo events
        db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).delete()
        
        today = date.today()
        
        events_to_seed = [
            # Today: Moderate Load (2 meetings)
            CalendarEvent(
                user_id=user_id,
                title="Daily Product Sync",
                start_time=datetime.combine(today, time(9, 30)),
                end_time=datetime.combine(today, time(10, 15)),
                event_category="meeting",
                cognitive_weight=1.0,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="Engineering Architecture Review",
                start_time=datetime.combine(today, time(14, 0)),
                end_time=datetime.combine(today, time(15, 30)),
                event_category="meeting",
                cognitive_weight=1.5,
                is_fixed=True
            ),

            # Tomorrow: Heavy / Overloaded Day (4 meetings back-to-back)
            CalendarEvent(
                user_id=user_id,
                title="Client Quarterly Review",
                start_time=datetime.combine(today + timedelta(days=1), time(9, 0)),
                end_time=datetime.combine(today + timedelta(days=1), time(10, 30)),
                event_category="meeting",
                cognitive_weight=1.5,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="Hiring & Interview: Staff Architect",
                start_time=datetime.combine(today + timedelta(days=1), time(11, 0)),
                end_time=datetime.combine(today + timedelta(days=1), time(12, 0)),
                event_category="meeting",
                cognitive_weight=1.2,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="All-Hands Company Meeting",
                start_time=datetime.combine(today + timedelta(days=1), time(13, 30)),
                end_time=datetime.combine(today + timedelta(days=1), time(15, 0)),
                event_category="meeting",
                cognitive_weight=1.0,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="Vendor Contract Negotiation",
                start_time=datetime.combine(today + timedelta(days=1), time(16, 0)),
                end_time=datetime.combine(today + timedelta(days=1), time(17, 30)),
                event_category="meeting",
                cognitive_weight=1.5,
                is_fixed=True
            ),

            # Day 2: Green Focus Day (Only 1 short morning sync)
            CalendarEvent(
                user_id=user_id,
                title="Quick 15-min Standup",
                start_time=datetime.combine(today + timedelta(days=2), time(9, 15)),
                end_time=datetime.combine(today + timedelta(days=2), time(9, 30)),
                event_category="meeting",
                cognitive_weight=0.8,
                is_fixed=True
            ),

            # Day 3: Light Day
            CalendarEvent(
                user_id=user_id,
                title="Design System Review",
                start_time=datetime.combine(today + timedelta(days=3), time(11, 0)),
                end_time=datetime.combine(today + timedelta(days=3), time(12, 0)),
                event_category="meeting",
                cognitive_weight=1.0,
                is_fixed=True
            ),
        ]

        db.add_all(events_to_seed)
        db.commit()

    @staticmethod
    def get_google_auth_url(user_id: str, redirect_uri: str) -> str:
        """
        Builds the Google OAuth 2.0 authorization URL.
        """
        import urllib.parse
        from app.config import settings

        client_id = settings.google_client_id
        scope = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.readonly"
        
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent",
            "state": user_id
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchanges authorization code for access and refresh tokens.
        """
        import httpx
        from app.config import settings

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=payload)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text, "status_code": resp.status_code}

    @staticmethod
    async def sync_google_events(db: Session, user_id: str, access_token: str, days: int = 7) -> int:
        """
        Pulls upcoming events from user's primary Google Calendar and syncs with database.
        """
        import httpx

        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days)).isoformat() + "Z"

        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                return 0

            data = resp.json()
            items = data.get("items", [])
            synced_count = 0

            for item in items:
                title = item.get("summary", "Untitled Meeting")
                start_raw = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                end_raw = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")

                if not start_raw:
                    continue

                # Parse datetime (handling ISO format with tz)
                try:
                    start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else start_dt + timedelta(minutes=30)
                except Exception:
                    continue

                # Deduplicate or add
                existing = db.query(CalendarEvent).filter(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.title == title,
                    CalendarEvent.start_time == start_dt.replace(tzinfo=None)
                ).first()

                if not existing:
                    ev = CalendarEvent(
                        user_id=user_id,
                        title=title,
                        description=item.get("description", ""),
                        location=item.get("location", ""),
                        start_time=start_dt.replace(tzinfo=None),
                        end_time=end_dt.replace(tzinfo=None),
                        event_category="meeting",
                        cognitive_weight=1.0,
                        is_fixed=True
                    )
                    db.add(ev)
                    synced_count += 1

            db.commit()
            return synced_count

    @staticmethod
    async def create_google_event(
        access_token: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Creates a new event directly on Google Calendar.
        """
        import httpx

        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time.isoformat() + "Z"},
            "end": {"dateTime": end_time.isoformat() + "Z"}
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=body)
            return resp.json()

