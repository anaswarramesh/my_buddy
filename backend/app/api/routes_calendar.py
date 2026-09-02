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
def delete_event(event_id: str, db: Session = Depends(get_db)):
    ev = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    
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

    # Sync events for upcoming 7 days
    synced_count = await CalendarService.sync_google_events(db, user_id, access_token, days=7)

    return HTMLResponse(f"""
    <html>
        <head><title>Google Calendar Connected</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 40px;">
            <div style="max-width: 500px; margin: auto; padding: 30px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <h2 style="color: #10B981; margin-top: 0;">Google Calendar Connected!</h2>
                <p>Successfully synced <strong>{synced_count}</strong> upcoming events into CoachPilot AI.</p>
                <p style="color: #666; font-size: 14px;">Your Waveshare ESP32-S3 Mini desk companion and mobile dashboard now reflect your live calendar density.</p>
                <a href="/" style="display: inline-block; margin-top: 15px; padding: 10px 20px; background: #2563EB; color: #fff; text-decoration: none; border-radius: 8px;">Go to Dashboard</a>
            </div>
        </body>
    </html>
    """)

