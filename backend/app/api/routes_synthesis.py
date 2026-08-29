from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from typing import Dict, Any, List
from app.database import get_db
from app.models.task import Task
from app.services.calendar_service import CalendarService
from app.services.density_service import DensityService
from app.schemas.calendar import CalendarEventResponse
from app.schemas.task import TaskResponse

router = APIRouter(prefix="/api/synthesis", tags=["Daily Synthesis Dashboard"])

@router.get("/daily")
def get_daily_synthesis(user_id: str = "default-user", db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Daily Morning Synthesis combining:
    - Today's Density Meter & Level
    - Today's Appointments
    - High-leverage Micro-Starter Tasks
    - AI Executive Coaching Nudge
    """
    today = date.today()
    events = CalendarService.get_events_for_range(db, user_id, today, today)
    density_res = DensityService.calculate_day_density(today, events)

    # Top starter / pending tasks
    starter_tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.status.in_(["pending", "scheduled"]),
        Task.is_starter_step == True
    ).limit(3).all()

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
