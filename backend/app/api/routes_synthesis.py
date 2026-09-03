from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from typing import Dict, Any, List, Optional
from app.database import get_db
from app.models.task import Task
from app.services.calendar_service import CalendarService
from app.services.density_service import DensityService
from app.schemas.calendar import CalendarEventResponse
from app.schemas.task import TaskResponse

router = APIRouter(prefix="/api/synthesis", tags=["Daily Synthesis Dashboard"])

@router.get("/daily")
def get_daily_synthesis(
    user_id: str = "default-user",
    target_date: Optional[date] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Daily Morning Synthesis combining:
    - Target Date's Density Meter & Level
    - Target Date's Appointments
    - High-leverage Micro-Starter Tasks
    - AI Executive Coaching Nudge
    """
    today = date.today()
    selected_date = target_date or today
    events = CalendarService.get_events_for_range(db, user_id, selected_date, selected_date)

    start_dt = datetime.combine(selected_date, time(0, 0, 0))
    end_dt = datetime.combine(selected_date, time(23, 59, 59))

    scheduled_for_date = db.query(Task).filter(
        Task.user_id == user_id,
        Task.is_scheduled == True,
        Task.status.in_(["pending", "scheduled"]),
        Task.scheduled_start >= start_dt,
        Task.scheduled_start <= end_dt
    ).all()

    # Merge calendar events and scheduled tasks for exact cognitive density (deduplicating tasks with events)
    density_events = list(events)
    existing_event_titles = {e.title.lower().replace("⚡", "").strip() for e in events}
    for t in scheduled_for_date:
        if t.scheduled_start and t.scheduled_end:
            clean_t_title = t.title.lower().replace("⚡", "").strip()
            if clean_t_title not in existing_event_titles:
                density_events.append({
                    "start_time": t.scheduled_start,
                    "end_time": t.scheduled_end,
                    "cognitive_weight": 1.0,
                    "is_all_day": False
                })

    density_res = DensityService.calculate_day_density(selected_date, density_events)

    # If tasks are specifically scheduled for this date, show them
    if scheduled_for_date:
        starter_tasks = [t for t in scheduled_for_date if t.is_starter_step]
        other_tasks = [t for t in scheduled_for_date if not t.is_starter_step]
    else:
        # Always return active tasks from backlog so tasks are visible and schedule-able for any clicked day
        starter_tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status.in_(["pending", "scheduled"]),
            Task.is_starter_step == True
        ).limit(5).all()

        other_tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status.in_(["pending", "scheduled"]),
            Task.is_starter_step == False
        ).limit(3).all()


    # Dynamic Coaching Nudge based on density
    if density_res.density_level in ["dense", "overloaded"]:
        coaching_nudge = "⚡ High-density day alert. Protect your boundaries: execute only essential meetings and float deep-work tasks to your upcoming Green Day."
    elif density_res.density_level == "light":
        coaching_nudge = "🟢 Green Day ahead! Your cognitive bandwidth is clear. Target your highest-leverage 15-minute idea starter action first."
    else:
        coaching_nudge = "🎯 Balanced schedule today. You have a solid 90-minute focus window this afternoon for execution."

    return {
        "date": today.isoformat(),
        "density": {
            "score": density_res.density_score,
            "level": density_res.density_level,
            "committed_minutes": density_res.total_committed_minutes,
            "meeting_count": density_res.meeting_count,
            "available_focus_windows": [w.model_dump() for w in density_res.available_focus_windows]
        },
        "today_events": [CalendarEventResponse.model_validate(e).model_dump() for e in events],
        "starter_tasks": [TaskResponse.model_validate(t).model_dump() for t in starter_tasks],
        "scheduled_tasks": [TaskResponse.model_validate(t).model_dump() for t in other_tasks],
        "coaching_nudge": coaching_nudge
    }
