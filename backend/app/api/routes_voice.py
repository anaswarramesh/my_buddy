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

    # Persist if BIG_IDEA
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

        db.commit()
        result.auto_action_summary = f"Created idea '{idea_db.title}' and generated {len(decomposed_tasks)} starter steps."

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
        result.auto_action_summary = f"Logged {len(result.extracted_tasks)} immediate task(s)."

    return result
