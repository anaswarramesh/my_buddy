from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from app.database import get_db
from app.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventResponse, CalendarEventCreate, CalendarSyncResponse
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
