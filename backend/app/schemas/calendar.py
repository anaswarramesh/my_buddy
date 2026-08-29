from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CalendarEventCreate(BaseModel):
    user_id: Optional[str] = "default-user"
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool = False
    is_fixed: bool = True
    event_category: str = "meeting"
    cognitive_weight: float = 1.0

class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    external_event_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool
    is_fixed: bool
    event_category: str
    cognitive_weight: float
    created_at: datetime
    updated_at: datetime

class CalendarSyncResponse(BaseModel):
    synced_events_count: int
    provider: str
    sync_status: str
    message: str
