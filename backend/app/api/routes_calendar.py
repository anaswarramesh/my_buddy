from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from app.database import get_db
from app.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventResponse, CalendarEventCreate, CalendarEventUpdate, CalendarSyncResponse
from app.schemas.density import DailyDensityResponse, MultiDayDensityResponse
from app.services.calendar_service import CalendarService
from app.services.density_service import DensityService

router = APIRouter(prefix="/api/calendar", tags=["Calendar & Density"])

@router.get("/events", response_model=List[CalendarEventResponse])
def get_events(
    user_id: str = "default-user",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    s_date = start_date or date.today()
    e_date = end_date or (s_date + timedelta(days=7))
    return CalendarService.get_events_for_range(db, user_id, s_date, e_date)

@router.post("/events", response_model=CalendarEventResponse)
def create_event(payload: CalendarEventCreate, db: Session = Depends(get_db)):
    ev = CalendarEvent(
        user_id=payload.user_id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_all_day=payload.is_all_day,
        is_fixed=payload.is_fixed,
        event_category=payload.event_category,
        cognitive_weight=payload.cognitive_weight
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev

@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
def update_event(event_id: str, payload: CalendarEventUpdate, db: Session = Depends(get_db)):
    ev = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(ev, field, val)
    
    db.commit()
    db.refresh(ev)
    return ev

@router.delete("/events/{event_id}")
async def delete_event(event_id: str, db: Session = Depends(get_db)):
    ev = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    
    # If this event was synced from Google Calendar, delete from Google Calendar too!
    if ev.external_event_id:
        try:
            token = await CalendarService.get_valid_google_token(db, ev.user_id)
            if token:
                await CalendarService.delete_google_event(token, ev.external_event_id)
        except Exception as e:
            print(f"[Google Delete] Error deleting from Google Calendar: {e}")

    db.delete(ev)
    db.commit()
    return {"status": "deleted", "id": event_id}

@router.delete("/clear-demo")
def clear_demo_events(user_id: str = "default-user", db: Session = Depends(get_db)):
    """
    Clears all seeded demo events, preserving real Google Calendar events and AI scheduled tasks.
    """
    count = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == user_id,
        CalendarEvent.external_event_id == None,
        CalendarEvent.event_category != "ai_starter_task"
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "cleared", "deleted_count": count, "message": f"Cleared {count} demo events."}

@router.get("/density", response_model=MultiDayDensityResponse)
def get_density_overview(
    user_id: str = "default-user",
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Computes rolling schedule density and available focus windows for upcoming days.
    """
    today = date.today()
    snapshots: List[DailyDensityResponse] = []
    green_days: List[date] = []

    for offset in range(days):
        cur_date = today + timedelta(days=offset)
        events = CalendarService.get_events_for_range(db, user_id, cur_date, cur_date)
        d_res = DensityService.calculate_day_density(cur_date, events)
        snapshots.append(d_res)
        if d_res.density_level == "light":
            green_days.append(cur_date)

    return MultiDayDensityResponse(
        user_id=user_id,
        snapshots=snapshots,
        green_day_candidates=green_days
    )

@router.post("/seed-demo", response_model=CalendarSyncResponse)
def seed_demo_calendar_endpoint(user_id: str = "default-user", db: Session = Depends(get_db)):
    """
    Populates realistic calendar data with heavy and light days to test auto-scheduling.
    """
    CalendarService.seed_demo_calendar(db, user_id)
    return CalendarSyncResponse(
        synced_events_count=8,
        provider="Google & CalDAV Mock Sync",
        sync_status="success",
        message="Demo calendar successfully synchronized with mixed density profiles."
    )

@router.get("/google/login")
def google_calendar_login(user_id: str = "default-user"):
    """
    Redirects user to Google OAuth 2.0 consent screen.
    """
    from fastapi.responses import RedirectResponse
    from app.config import settings

    redirect_uri = settings.google_redirect_uri or f"{settings.base_url}/api/calendar/google/callback"
    if not settings.google_client_id:
        raise HTTPException(status_code=400, detail="GOOGLE_CLIENT_ID is not configured in environment variables.")

    auth_url = CalendarService.get_google_auth_url(user_id, redirect_uri)
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_calendar_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    state: Optional[str] = "default-user",
    db: Session = Depends(get_db)
):
    """
    Receives OAuth 2.0 authorization code from Google, exchanges it for tokens, and performs initial event sync.
    """
    from fastapi.responses import HTMLResponse
    from app.config import settings

    if error:
        return HTMLResponse(f"<h3>Google Authorization Failed</h3><p>{error}</p>", status_code=400)

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing from Google callback.")

    redirect_uri = settings.google_redirect_uri or f"{settings.base_url}/api/calendar/google/callback"
    tokens = await CalendarService.exchange_code_for_tokens(code, redirect_uri)

    if "error" in tokens:
        return HTMLResponse(f"<h3>Token Exchange Failed</h3><p>{tokens.get('error')}</p>", status_code=400)

    access_token = tokens.get("access_token")
    user_id = state or "default-user"

    # Persist OAuth tokens so automatic and background sync works
    CalendarService.save_oauth_tokens(db, user_id, tokens, provider="google")

    # Sync events for upcoming 7 days
    synced_count = await CalendarService.sync_google_events(db, user_id, access_token, days=7)

    refresh_token = tokens.get("refresh_token", "")
    token_box_html = ""
    if refresh_token:
        token_box_html = f"""
        <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 14px; margin: 18px 0; text-align: left;">
            <p style="margin: 0 0 6px 0; font-size: 12px; font-weight: 700; color: #1e293b;">🔑 Permanent Auto-Connect Token:</p>
            <textarea readonly onclick="this.select()" style="width: 100%; height: 50px; font-size: 11px; font-family: monospace; color: #0f172a; background: #fff; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; resize: none;">{refresh_token}</textarea>
            <p style="margin: 6px 0 0 0; font-size: 11px; color: #64748b;">(Optional) Copy this and add it as Render Environment Variable <code>GOOGLE_REFRESH_TOKEN</code> to ensure Google Calendar auto-connects permanently on every future server reboot without clicking anything.</p>
        </div>
        """

    return HTMLResponse(f"""
    <html>
        <head><title>Google Calendar Connected</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 40px; background: #f1f5f9;">
            <div style="max-width: 520px; margin: auto; padding: 30px; background: #fff; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px rgba(0,0,0,0.06);">
                <div style="width: 50px; height: 50px; background: #ecfdf5; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;">
                    <span style="font-size: 24px; color: #10b981;">✓</span>
                </div>
                <h2 style="color: #0f172a; margin: 0 0 8px;">Google Calendar Connected!</h2>
                <p style="color: #475569; font-size: 14px; margin: 0 0 16px;">Successfully imported <strong>{synced_count}</strong> upcoming events into your CoachPilot schedule and ESP32 display.</p>
                {token_box_html}
                <a href="/" style="display: inline-block; margin-top: 10px; padding: 12px 24px; background: #2563EB; color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px;">Open Dashboard</a>
            </div>
        </body>
    </html>
    """)

@router.post("/google/sync")
async def sync_google_calendar_endpoint(user_id: str = "default-user", db: Session = Depends(get_db)):
    """
    Triggers an immediate on-demand synchronization with Google Calendar.
    """
    token = await CalendarService.get_valid_google_token(db, user_id)
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Google Calendar is not linked. Please click 'Connect Google Calendar' first."
        )

    synced_count = await CalendarService.sync_google_events(db, user_id, token, days=7)
    return {
        "status": "success",
        "synced_count": synced_count,
        "message": f"Successfully synchronized {synced_count} events from Google Calendar."
    }

@router.get("/google/status")
def get_google_sync_status(user_id: str = "default-user", db: Session = Depends(get_db)):
    """
    Checks if Google Calendar is connected and when it was last synced.
    """
    from app.models.oauth import OAuthCredential
    cred = db.query(OAuthCredential).filter(
        OAuthCredential.user_id == user_id,
        OAuthCredential.provider == "google"
    ).first()

    if not cred or not cred.access_token:
        return {"connected": False, "last_synced_at": None}

    return {
        "connected": True,
        "last_synced_at": cred.last_synced_at.isoformat() if cred.last_synced_at else None
    }

