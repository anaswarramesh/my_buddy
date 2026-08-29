from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.nlp import NLPCommandRequest, NLPCommandResponse
from app.services.llm_service import LLMService
from app.services.calendar_service import CalendarService
from app.services.density_service import DensityService
from app.models.task import Task
from datetime import date, timedelta

router = APIRouter(prefix="/api/nlp", tags=["Natural Language Rescheduling"])

@router.post("/command", response_model=NLPCommandResponse)
async def process_nlp_command(payload: NLPCommandRequest, db: Session = Depends(get_db)):
    """
    Executes Prompt C:
    Parses natural language commands like "Clear my Thursday afternoon and float those tasks to next week",
    analyzes current density, and mutates calendar/tasks accordingly.
    """
    today = date.today()
    # Gather 7-day density snapshots
    snapshots = []
    for offset in range(7):
        cur_date = today + timedelta(days=offset)
        events = CalendarService.get_events_for_range(db, payload.user_id, cur_date, cur_date)
        d_res = DensityService.calculate_day_density(cur_date, events)
        snapshots.append(d_res.model_dump())

    # Get active tasks
    tasks = db.query(Task).filter(Task.user_id == payload.user_id, Task.status != "completed").limit(5).all()
    tasks_dicts = [{"id": t.id, "title": t.title, "friction": t.friction_level} for t in tasks]

    return await LLMService.analyze_density_and_nlp(
        command=payload.command,
        density_snapshots=snapshots,
        existing_tasks=tasks_dicts
    )
