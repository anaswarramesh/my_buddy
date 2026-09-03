from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.database import Base, engine, SessionLocal
from app.models import User, Idea, Task, CalendarEvent, DailyDensitySnapshot
from app.services.calendar_service import CalendarService
from app.api.routes_voice import router as voice_router
from app.api.routes_ideas import router as ideas_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_calendar import router as calendar_router
from app.api.routes_synthesis import router as synthesis_router
from app.api.routes_nlp import router as nlp_router
from app.api.routes_hardware import router as hardware_router

import asyncio

# Initialize Tables
Base.metadata.create_all(bind=engine)

async def background_google_sync_worker():
    """
    Background worker that runs continuously and syncs Google Calendar events
    every 5 minutes without needing any manual user intervention.
    """
    while True:
        try:
            await asyncio.sleep(300) # Wait 5 minutes between syncs
            db = SessionLocal()
            try:
                token = await CalendarService.get_valid_google_token(db, "default-user")
                if token:
                    print("[Background Worker] Auto-syncing Google Calendar in background...")
                    await CalendarService.sync_google_events(db, "default-user", token, days=7)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Background Worker] Google Calendar sync loop error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed default user and auto-sync on startup
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == "default-user").first()
        if not user:
            user = User(
                id="default-user",
                email="builder@coachpilot.ai",
                full_name="Alex Builder",
                timezone="America/New_York",
                coaching_style="proactive_challenger"
            )
            db.add(user)
            db.commit()
            print("[Startup] Initialized default user Alex Builder.")
        
        # Initial Google Calendar auto-sync on startup / restart
        try:
            token = await CalendarService.get_valid_google_token(db, "default-user")
            if token:
                print("[Startup] Auto-syncing Google Calendar on restart...")
                await CalendarService.sync_google_events(db, "default-user", token, days=7)
        except Exception as e:
            print(f"[Startup] Initial Google sync: {e}")
    finally:
        db.close()

    # Launch background worker
    sync_task = asyncio.create_task(background_google_sync_worker())
    yield
    sync_task.cancel()

app = FastAPI(
    title="CoachPilot AI - Daily Productivity & Coaching Assistant",
    description="Backend API supporting Voice Ingestion, Idea Feasibility Coaching, Schedule Density Auto-Placement, and Hardware IoT OLED displays.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(voice_router)
app.include_router(ideas_router)
app.include_router(tasks_router)
app.include_router(calendar_router)
app.include_router(synthesis_router)
app.include_router(nlp_router)
app.include_router(hardware_router)

# Mount static preview directory if exists
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {
        "app": "CoachPilot AI Backend",
        "status": "online",
        "endpoints": {
            "synthesis": "/api/synthesis/daily",
            "voice_process": "/api/voice/process-thought",
            "hardware_display": "/api/hardware/display-data",
            "calendar_density": "/api/calendar/density",
            "ideas": "/api/ideas",
            "nlp_command": "/api/nlp/command",
            "docs": "/docs"
        }
    }
