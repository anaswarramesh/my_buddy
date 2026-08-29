from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class IdeaAnalysis(BaseModel):
    title: str
    category: str = "business"
    summary: str
    feasibility_score: int
    impact_score: int
    friction_score: int
    primary_obstacle: Optional[str] = None
    coaching_verdict: Optional[str] = None
    nudge_strategy: Optional[str] = None

class IdeaCreate(BaseModel):
    user_id: Optional[str] = "default-user"
    raw_transcript: str
    title: str
    summary: Optional[str] = None
    category: Optional[str] = "business"
    feasibility_score: Optional[int] = 50
    impact_score: Optional[int] = 50
    friction_score: Optional[int] = 50
    coaching_verdict: Optional[str] = None
    primary_obstacle: Optional[str] = None
    nudge_strategy: Optional[str] = None

class IdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    raw_transcript: str
    title: str
    summary: Optional[str] = None
    category: str
    feasibility_score: int
    impact_score: int
    friction_score: int
    coaching_verdict: Optional[str] = None
    primary_obstacle: Optional[str] = None
    nudge_strategy: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

class IdeaDecompositionResponse(BaseModel):
    idea_id: str
    tasks_generated: int
    starter_step_title: str
    coaching_message: str
