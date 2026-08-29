from typing import Optional, List
from pydantic import BaseModel
from app.schemas.idea import IdeaAnalysis
from app.schemas.task import TaskCreate

class VoiceTranscribeRequest(BaseModel):
    audio_base64: Optional[str] = None
    language: Optional[str] = "en"

class VoiceTranscribeResponse(BaseModel):
    transcript: str
    duration_seconds: Optional[float] = 0.0

class VoiceProcessThoughtRequest(BaseModel):
    user_id: Optional[str] = "default-user"
    transcript: str

class VoiceProcessThoughtResponse(BaseModel):
    classification: str # BIG_IDEA, IMMEDIATE_TASK, CALENDAR_COMMAND, HYBRID
    confidence: float
    transcript: str
    idea_analysis: Optional[IdeaAnalysis] = None
    extracted_tasks: List[TaskCreate] = []
    coaching_nudge: Optional[str] = None
    auto_action_summary: Optional[str] = None
