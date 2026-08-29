from typing import List, Optional
from datetime import date
from pydantic import BaseModel

class FocusWindow(BaseModel):
    start_time: str # "HH:MM"
    end_time: str   # "HH:MM"
    duration_minutes: int
    suitability: str # "deep_work", "starter_task", "admin"

class DailyDensityResponse(BaseModel):
    date: date
    density_score: float # 0.00 to 1.00
    density_level: str   # 'light', 'moderate', 'dense', 'overloaded'
    total_committed_minutes: int
    meeting_count: int
    available_focus_windows: List[FocusWindow]

class MultiDayDensityResponse(BaseModel):
    user_id: str
    snapshots: List[DailyDensityResponse]
    green_day_candidates: List[date]
