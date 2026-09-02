from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.voice import (
    VoiceTranscribeRequest,
    VoiceTranscribeResponse,
    VoiceProcessThoughtRequest,
    VoiceProcessThoughtResponse
)
from app.services.whisper_service import WhisperService
from app.services.llm_service import LLMService
from app.models.idea import Idea
from app.models.task import Task
from app.models.user import User
from app.models.calendar import CalendarEvent
from app.services.calendar_service import CalendarService
from app.services.density_service import DensityService
from app.services.scheduler_service import SchedulerService
from app.services.event_parser import EventParserService
from datetime import date, timedelta

router = APIRouter(prefix="/api/voice", tags=["Voice Processing"])

@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_audio_endpoint(
    file: Optional[UploadFile] = File(None),
    payload: Optional[VoiceTranscribeRequest] = None
):
    """
    Accepts raw audio file or base64 data and returns transcription via Whisper.
    """
    audio_bytes = None
    if file:
        audio_bytes = await file.read()
    
    base64_str = payload.audio_base64 if payload else None
    transcript = await WhisperService.transcribe_audio(audio_bytes=audio_bytes, audio_base64=base64_str)
    
    return VoiceTranscribeResponse(
        transcript=transcript,
        duration_seconds=12.5
    )

@router.post("/process-thought", response_model=VoiceProcessThoughtResponse)
async def process_thought_endpoint(
    payload: VoiceProcessThoughtRequest,
    db: Session = Depends(get_db)
):
    """
    Processes raw voice transcript through Prompt A:
    - Triages into BIG_IDEA vs IMMEDIATE_TASK vs CALENDAR_COMMAND
    - Evaluates feasibility, friction, and coaching strategy for ideas
    - Automatically persists new Idea and starter steps in database
    """
    # Ensure default user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        user = User(id=payload.user_id, email="demo@coachpilot.ai", full_name="Alex Builder")
        db.add(user)
        db.commit()

    # Call LLM Prompt A
    result = await LLMService.classify_and_coach(
        transcript=payload.transcript,
        user_timezone=user.timezone,
        coaching_persona=user.coaching_style
    )

    # 1. First, check if voice transcript contains an explicit meeting or appointment with a time
    parsed_event = EventParserService.parse_event_from_text(payload.transcript)
    if parsed_event:
        cal_event = CalendarEvent(
            user_id=user.id,
            title=parsed_event["title"],
            start_time=parsed_event["start_dt"],
            end_time=parsed_event["end_dt"],
            is_fixed=True,
            event_category="voice_meeting",
            cognitive_weight=parsed_event["cognitive_weight"]
        )
        db.add(cal_event)
        db.commit()
        db.refresh(cal_event)

        # Push to Google Calendar if linked
        google_token = await CalendarService.get_valid_google_token(db, user.id)
        if google_token:
            try:
                await CalendarService.create_google_event(
                    access_token=google_token,
                    title=cal_event.title,
                    start_time=cal_event.start_time,
                    end_time=cal_event.end_time,
                    description="Scheduled via CoachPilot AI Voice"
                )
            except Exception as e:
                print(f"[Google Calendar] Failed to push voice event: {e}")

        result.classification = "CALENDAR_COMMAND"
        result.auto_action_summary = f"Booked '{cal_event.title}' on {cal_event.start_time.strftime('%A, %b %d at %I:%M %p')}."
        result.coaching_nudge = f"Scheduled '{cal_event.title}' directly into your calendar."
        return result

    # 2. Persist if BIG_IDEA
    if result.classification in ["BIG_IDEA", "HYBRID"] and result.idea_analysis:
        idea_db = Idea(
            user_id=user.id,
            raw_transcript=payload.transcript,
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

        # Generate starter tasks via Prompt B
        decomposed_tasks = await LLMService.decompose_idea(
            idea_title=idea_db.title,
            idea_summary=idea_db.summary,
            coaching_verdict=idea_db.coaching_verdict,
            primary_obstacle=idea_db.primary_obstacle
        )

        starter_task_db = None
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
                starter_task_db = task_db

        db.commit()

        # Auto-schedule starter action into calendar
        if starter_task_db:
            db.refresh(starter_task_db)
            SchedulerService.auto_schedule_task(db, user.id, starter_task_db)

        result.auto_action_summary = f"Created idea '{idea_db.title}' and scheduled 15m micro-ignition action into your calendar."

    elif result.classification == "IMMEDIATE_TASK":
        for t in result.extracted_tasks:
            task_db = Task(
                user_id=user.id,
                title=t.title,
                description=t.description,
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
            SchedulerService.auto_schedule_task(db, user.id, task_db)

        result.auto_action_summary = f"Logged and auto-scheduled {len(result.extracted_tasks)} task(s) into your focus window."

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
            command=payload.transcript,
            density_snapshots=snapshots,
            existing_tasks=tasks_dicts
        )
        result.auto_action_summary = nlp_res.nlp_summary

    return result
