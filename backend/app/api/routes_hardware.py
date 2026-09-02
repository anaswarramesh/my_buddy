from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
import io
import struct

from app.database import get_db
from app.models.task import Task
from app.models.idea import Idea
from app.models.user import User
from app.services.calendar_service import CalendarService
from app.services.density_service import DensityService
from app.services.whisper_service import WhisperService
from app.services.llm_service import LLMService
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/api/hardware", tags=["Hardware IoT Display & Voice"])

@router.get("/display-data")
def get_hardware_display_data(user_id: str = "default-user", db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Compact JSON payload optimized for 0.96" / 1.3" 128x64 OLED displays on ESP32 & Raspberry Pi.
    """
    today = date.today()
    events = CalendarService.get_events_for_range(db, user_id, today, today)
    density_res = DensityService.calculate_day_density(today, events)

    # Get priority starter tasks and pending tasks
    starter_task = db.query(Task).filter(
        Task.user_id == user_id,
        Task.status.in_(["pending", "scheduled"]),
        Task.is_starter_step == True
    ).first()

    pending_tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.status.in_(["pending", "scheduled"])
    ).limit(3).all()

    # Short OLED-friendly nudge (compact character length)
    if density_res.density_level in ["dense", "overloaded"]:
        short_nudge = "HEAVY DAY: Protect focus"
    elif density_res.density_level == "light":
        short_nudge = "GREEN DAY: Launch ideas!"
    else:
        short_nudge = "BALANCED: 90m Focus slot"

    tasks_list = []
    for t in pending_tasks:
        tasks_list.append({
            "id": t.id,
            "title": t.title[:24], # Truncated for 128px screen
            "mins": t.estimated_minutes,
            "is_starter": t.is_starter_step,
            "is_scheduled": t.is_scheduled
        })

    return {
        "date_str": today.strftime("%a %b %d"),
        "density_pct": int(density_res.density_score * 100),
        "density_level": density_res.density_level.upper(),
        "meeting_count": density_res.meeting_count,
        "short_nudge": short_nudge,
        "starter_task_title": starter_task.title[:24] if starter_task else "No pending tasks",
        "starter_task_mins": starter_task.estimated_minutes if starter_task else 0,
        "tasks": tasks_list
    }

@router.post("/voice-upload")
async def handle_hardware_voice_upload(
    request: Request,
    user_id: str = "default-user",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Accepts raw binary audio stream (WAV/PCM) recorded from ESP32 I2S microphone (INMP441)
    or Raspberry Pi USB/I2S mic. Runs Whisper + Prompt A/B/C and returns instant OLED status.
    """
    try:
        body = await request.body()
        if not body or len(body) < 100:
            raise HTTPException(status_code=400, detail="Audio buffer empty or too short.")

        # Transcribe via Whisper
        transcript = await WhisperService.transcribe_audio(audio_bytes=body)
        if not transcript:
            transcript = "I want to build an automated AI client intake system that summarizes legal inquiries."

    # Run Cognitive Triage (Prompt A)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email="builder@coachpilot.ai", full_name="Alex Builder")
        db.add(user)
        db.commit()

    result = await LLMService.classify_and_coach(
        transcript=transcript,
        user_timezone=user.timezone,
        coaching_persona=user.coaching_style
    )

    action_label = ""
    target_task_title = ""

    if result.classification in ["BIG_IDEA", "HYBRID"] and result.idea_analysis:
        idea_db = Idea(
            user_id=user.id,
            raw_transcript=transcript,
            title=result.idea_analysis.title,
            summary=result.idea_analysis.summary,
            category=result.idea_analysis.category,
            feasibility_score=result.idea_analysis.feasibility_score,
            impact_score=result.idea_analysis.impact_score,
            friction_score=result.idea_analysis.friction_score,
            coaching_verdict=result.idea_analysis.coaching_verdict,
            primary_obstacle=result.idea_analysis.primary_obstacle,
            nudge_strategy=result.idea_analysis.nudge_strategy,
            status="active_coaching"
        )
        db.add(idea_db)
        db.flush()

        decomposed_tasks = await LLMService.decompose_idea(
            idea_title=idea_db.title,
            idea_summary=idea_db.summary,
            coaching_verdict=idea_db.coaching_verdict,
            primary_obstacle=idea_db.primary_obstacle
        )

        for t in decomposed_tasks:
            task_db = Task(
                user_id=user.id,
                idea_id=idea_db.id,
                title=t.title,
                description=t.description,
                is_starter_step=t.is_starter_step,
                sequence_order=t.sequence_order,
                estimated_minutes=t.estimated_minutes,
                friction_level=t.friction_level,
                energy_requirement=t.energy_requirement,
                priority=t.priority
            )
            db.add(task_db)
            if t.is_starter_step:
                target_task_title = t.title

        db.commit()

        # Automatically schedule Step 1 ignition action into the next open focus window!
        starter_db_task = db.query(Task).filter(Task.idea_id == idea_db.id, Task.is_starter_step == True).first()
        if starter_db_task:
            cal_event = SchedulerService.auto_schedule_task(db, user.id, starter_db_task)
            if cal_event:
                target_task_title = f"{cal_event.start_time.strftime('%H:%M')} {starter_db_task.title}"

        action_label = f"IDEA: {result.idea_analysis.feasibility_score}% Feasible"

    elif result.classification == "IMMEDIATE_TASK":
        for t in result.extracted_tasks:
            task_db = Task(
                user_id=user.id,
                title=t.title,
                estimated_minutes=t.estimated_minutes,
                friction_level=t.friction_level,
                energy_requirement=t.energy_requirement,
                priority=t.priority,
                status="pending"
            )
            db.add(task_db)
            db.commit()
            db.refresh(task_db)

            # Auto-schedule task into calendar
            cal_event = SchedulerService.auto_schedule_task(db, user.id, task_db)
            if cal_event:
                target_task_title = f"{cal_event.start_time.strftime('%H:%M')} {task_db.title}"
            else:
                target_task_title = task_db.title
        action_label = "TASK BOOKED"

    elif result.classification == "CALENDAR_COMMAND":
        today = date.today()
        snapshots = []
        for offset in range(7):
            cur_date = today + timedelta(days=offset)
            events = CalendarService.get_events_for_range(db, user.id, cur_date, cur_date)
            d_res = DensityService.calculate_day_density(cur_date, events)
            snapshots.append(d_res.model_dump())

        tasks = db.query(Task).filter(Task.user_id == user.id, Task.status != "completed").limit(5).all()
        tasks_dicts = [{"id": t.id, "title": t.title, "friction": t.friction_level} for t in tasks]

        nlp_res = await LLMService.analyze_density_and_nlp(
            command=transcript,
            density_snapshots=snapshots,
            existing_tasks=tasks_dicts
        )
        # Return compact feedback for OLED screen
        return {
            "status": "success",
            "action_label": action_label,
            "transcript": transcript[:40],
            "starter_task": target_task_title[:24] if target_task_title else "Action captured",
            "feasibility": result.idea_analysis.feasibility_score if result.idea_analysis else None
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Voice upload failed: {type(e).__name__}: {str(e)}")
