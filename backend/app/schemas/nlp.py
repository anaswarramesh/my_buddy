from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class NLPCommandRequest(BaseModel):
    user_id: Optional[str] = "default-user"
    command: str

class NLPMutationDetail(BaseModel):
    action: str # "RESCHEDULE_TASK", "SCHEDULE_STARTER_TASK", "CLEAR_WINDOW", "FLOAT_TASKS"
    item_id: Optional[str] = None
    item_title: str
    previous_start: Optional[datetime] = None
    new_start: Optional[datetime] = None
    new_end: Optional[datetime] = None
    reason: str

class NLPCommandResponse(BaseModel):
    original_command: str
    summary_of_changes: str
    mutations: List[NLPMutationDetail]
    coaching_nudge: Optional[str] = None
    density_impact_summary: Optional[str] = None
