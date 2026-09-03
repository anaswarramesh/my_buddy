from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta
from typing import Dict, Any, List, Optional
import io
import os
import struct

LATEST_AUDIO_PATH = "/tmp/latest_hardware_voice.wav"

from app.database import get_db
from app.models.task import Task
from app.models.idea import Idea
from app.models.user import User
from app.models.calendar import CalendarEvent
from app.services.calendar_service import CalendarService
from app.services.density_service import DensityService
from app.services.whisper_service import WhisperService
from app.services.llm_service import LLMService
from app.services.scheduler_service import SchedulerService
from app.services.event_parser import EventParserService

router = APIRouter(prefix="/api/hardware", tags=["Hardware IoT Display & Voice"])

@router.get("/display-data")
async def get_hardware_display_data(user_id: str = "default-user", db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Compact JSON payload optimized for 0.96" / 1.3" 128x64 OLED displays on ESP32 & Raspberry Pi.
    Merges both calendar events and voice-scheduled tasks into the OLED timeline and load calculation.
    Automatically background-syncs with Google Calendar if connected.
    """
    # Auto-sync Google Calendar in background if linked and not synced in last 3 minutes
    try:
        from app.models.oauth import OAuthCredential
        cred = db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.provider == "google"
        ).first()
        should_sync = False
        if not cred or not cred.last_synced_at:
            should_sync = True
        elif cred.last_synced_at < datetime.utcnow() - timedelta(minutes=3):
            should_sync = True

        if should_sync:
            token = await CalendarService.get_valid_google_token(db, user_id)
            if token:
                print(f"[Hardware Auto-Sync] Automatically syncing Google Calendar for {user_id}...")
                await CalendarService.sync_google_events(db, user_id, token, days=7)
    except Exception as sync_err:
        print(f"[Hardware Auto-Sync] Sync check failed: {sync_err}")

    today = date.today()
    start_of_day = datetime.combine(today, time(0, 0, 0))
    end_of_day = datetime.combine(today, time(23, 59, 59))

    events = CalendarService.get_events_for_range(db, user_id, today, today)
    
    # Fetch scheduled tasks for today
    scheduled_tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.is_scheduled == True,
        Task.scheduled_start >= start_of_day,
        Task.scheduled_start <= end_of_day
    ).all()

    # Get priority starter tasks and pending tasks
    starter_task = db.query(Task).filter(
        Task.user_id == user_id,
        Task.status.in_(["pending", "scheduled"]),
        Task.is_starter_step == True
    ).first()

    pending_tasks = db.query(Task).filter(
        Task.user_id == user_id,
        Task.status.in_(["pending", "scheduled"])
    ).limit(4).all()

    # Calculate combined committed minutes
    event_mins = sum(int((e.end_time - e.start_time).total_seconds() / 60) for e in events)
    task_mins = sum(t.estimated_minutes for t in scheduled_tasks)
    total_committed = event_mins + task_mins
    
    # Work day = 540 minutes (9 hours)
    density_pct = min(100, int((total_committed / 540.0) * 100))
    if density_pct >= 75:
        density_level = "HEAVY"
        short_nudge = "HEAVY DAY: Protect focus"
    elif density_pct >= 40:
        density_level = "MODERATE"
        short_nudge = "BALANCED: 90m Focus slot"
    elif density_pct > 0:
        density_level = "LIGHT"
        short_nudge = "GREEN DAY: Focus on tasks"
    else:
        density_level = "CLEAR"
        short_nudge = "CLEAR DAY: Speak new tasks"

    # Merge calendar events and scheduled tasks into a unified timeline
    timeline_items = []
    for ev in events:
        clean_title = ev.title.replace("⚡", "").replace("🎙️", "").strip()
        timeline_items.append({
            "time": ev.start_time.strftime("%H:%M"),
            "start_dt": ev.start_time,
            "title": clean_title[:14]
        })
    for t in scheduled_tasks:
        time_str = t.scheduled_start.strftime("%H:%M") if t.scheduled_start else "Task"
        clean_title = t.title.replace("⚡", "").replace("🎙️", "").strip()
        # Avoid duplicate if an event and task have same title
        if not any(item["title"] == clean_title[:14] for item in timeline_items):
            timeline_items.append({
                "time": time_str,
                "start_dt": t.scheduled_start or start_of_day,
                "title": clean_title[:14]
            })

    # If fewer than 3 items, show pending tasks as TODO
    if len(timeline_items) < 3:
        for t in pending_tasks:
            clean_title = t.title.replace("⚡", "").replace("🎙️", "").strip()
            if not any(item["title"] == clean_title[:14] for item in timeline_items):
                timeline_items.append({
                    "time": "TODO",
                    "start_dt": end_of_day,
                    "title": clean_title[:14]
                })

    timeline_items.sort(key=lambda x: x["start_dt"])
    events_list = [{"time": item["time"], "title": item["title"]} for item in timeline_items[:4]]

    tasks_list = []
    for t in pending_tasks:
        tasks_list.append({
            "id": t.id,
            "title": t.title[:24],
            "mins": t.estimated_minutes,
            "is_starter": t.is_starter_step,
            "is_scheduled": t.is_scheduled
        })

    return {
        "date_str": today.strftime("%a %b %d"),
        "density_pct": density_pct,
        "density_level": density_level,
        "meeting_count": len(events) + len(scheduled_tasks),
        "short_nudge": short_nudge,
        "starter_task_title": starter_task.title[:24] if starter_task else (pending_tasks[0].title[:24] if pending_tasks else "No pending tasks"),
        "starter_task_mins": starter_task.estimated_minutes if starter_task else (pending_tasks[0].estimated_minutes if pending_tasks else 0),
        "events": events_list,
        "tasks": tasks_list
    }

@router.post("/voice-diag")
async def voice_diagnostics(request: Request):
    from app.config import settings
    import base64
    body = await request.body()
    result = {
        "audio_bytes_received": len(body),
        "gemini_api_key_set": bool(settings.gemini_api_key),
        "openai_api_key_set": bool(settings.openai_api_key)
    }
    if settings.gemini_api_key and len(body) > 200:
        import httpx
        models = [
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-2.5-flash-lite",
            "gemini-pro-latest",
            "gemini-3.6-flash"
        ]
        result["attempts"] = []
        try:
            encoded_audio = base64.b64encode(body).decode("utf-8")
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "audio/wav",
                                    "data": encoded_audio
                                }
                            },
                            {
                                "text": "Transcribe the spoken audio verbatim into English text. Return ONLY the transcribed words."
                            }
                        ]
                    }
                ]
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                for m in models:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={settings.gemini_api_key}"
                    try:
                        resp = await client.post(url, json=payload)
                        attempt = {"model": m, "status": resp.status_code}
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    attempt["text"] = parts[0].get("text", "")
                        else:
                            attempt["error"] = resp.text[:200]
                        result["attempts"].append(attempt)
                        if "text" in attempt and attempt["text"].strip():
                            result["successful_model"] = m
                            result["transcript"] = attempt["text"].strip()
                            break
                    except Exception as me:
                        result["attempts"].append({"model": m, "error": str(me)})
        except Exception as e:
            result["gemini_error"] = str(e)
    return result

@router.get("/latest-audio")
def get_latest_hardware_audio():
    """
    Streams the most recent audio recording uploaded by the ESP32 hardware
    so the user can listen to microphone quality directly in browser.
    """
    if os.path.exists(LATEST_AUDIO_PATH):
        return FileResponse(LATEST_AUDIO_PATH, media_type="audio/wav", filename="latest_hardware_voice.wav")
    raise HTTPException(status_code=404, detail="No audio recorded yet. Hold the button and speak into the ESP32 mic first.")

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

        # Persist latest audio for in-browser listening and debugging
        try:
            with open(LATEST_AUDIO_PATH, "wb") as f:
                f.write(body)
        except Exception as e:
            print(f"[Hardware] Could not save debug audio: {e}")

        # Check peak amplitude and duration to detect silence or accidental button taps
        max_amp = 0
        data_offset = 44 if body.startswith(b"RIFF") else 0
        raw_pcm = body[data_offset:]
        duration_secs = len(raw_pcm) / (16000 * 2) if len(raw_pcm) > 0 else 0
        if len(raw_pcm) >= 2:
            sample_count = len(raw_pcm) // 2
            samples = struct.unpack(f"<{sample_count}h", raw_pcm[:sample_count*2])
            max_amp = max(abs(s) for s in samples) if samples else 0
        print(f"[Hardware] Voice upload received: {len(body)} bytes ({duration_secs:.2f}s), Peak Amp: {max_amp}")

        # Reject accidental taps (<0.8s) or near-silence (<350 peak amplitude)
        if duration_secs < 0.8 or max_amp < 350:
            print(f"[Hardware] Rejected silence/tap: {duration_secs:.2f}s, Peak: {max_amp}")
            return {
                "status": "warning",
                "action_label": "NO SPEECH",
                "transcript": "No speech detected (hold button & speak)",
                "starter_task": "Hold button & speak",
                "feasibility": None
            }

        # Transcribe via Whisper / Gemini
        transcript = await WhisperService.transcribe_audio(audio_bytes=body)
        if not transcript or not transcript.strip():
            return {
                "status": "warning",
                "action_label": "VOICE UNCLEAR",
                "transcript": "Could not recognize words - speak louder/closer",
                "starter_task": "Speak closer to mic",
                "feasibility": None
            }

        # Ensure user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, email="builder@coachpilot.ai", full_name="Alex Builder")
            db.add(user)
            db.commit()

        # 1. Check if voice audio specifies an explicit meeting / appointment
        parsed_event = EventParserService.parse_event_from_text(transcript)
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

            # Also create a Task record so it appears in the user's tasks list!
            duration = max(15, int((cal_event.end_time - cal_event.start_time).total_seconds() / 60))
            task_db = Task(
                user_id=user.id,
                title=cal_event.title,
                estimated_minutes=duration,
                is_scheduled=True,
                scheduled_start=cal_event.start_time,
                scheduled_end=cal_event.end_time,
                status="scheduled",
                priority="high",
                friction_level="easy",
                energy_requirement="focus"
            )
            db.add(task_db)
            db.commit()

            # Sync to Google Calendar if connected
            google_token = await CalendarService.get_valid_google_token(db, user.id)
            if google_token:
                try:
                    await CalendarService.create_google_event(
                        access_token=google_token,
                        title=cal_event.title,
                        start_time=cal_event.start_time,
                        end_time=cal_event.end_time,
                        description="Scheduled via CoachPilot ESP32 Voice"
                    )
                except Exception as e:
                    print(f"[Google Calendar] Hardware voice sync failed: {e}")

            time_str = cal_event.start_time.strftime("%H:%M")
            return {
                "status": "success",
                "action_label": f"MTG: {time_str}",
                "transcript": transcript[:40],
                "starter_task": f"{time_str} {cal_event.title}"[:24],
                "feasibility": None
            }

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

            starter_db_task = None
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
                    starter_db_task = task_db

            db.commit()

            # Automatically schedule Step 1 ignition action into the next open focus window!
            if starter_db_task:
                db.refresh(starter_db_task)
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
            action_label = "CALENDAR SHIFTED"
            target_task_title = nlp_res.nlp_summary[:24]

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
