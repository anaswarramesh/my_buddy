from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class TaskCreate(BaseModel):
    user_id: Optional[str] = "default-user"
    idea_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    is_starter_step: bool = False
    sequence_order: int = 1
    estimated_minutes: int = 30
    friction_level: str = "easy" # micro, easy, medium, deep_work
    energy_requirement: str = "admin" # creative, deep_focus, admin, low_energy
    priority: str = "medium" # critical, high, medium, low
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    deadline: Optional[datetime] = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    idea_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    is_starter_step: bool
    sequence_order: int
    estimated_minutes: int
    friction_level: str
    energy_requirement: str
    priority: str
    is_scheduled: bool
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

class TaskScheduleRequest(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime
    create_calendar_event: bool = True
