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

# Initialize Tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed default user and demo calendar
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
    finally:
        db.close()
    yield

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
        return FileResponse(index_path)
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
