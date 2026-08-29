import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, ForeignKey
from app.database import Base

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    external_event_id = Column(String(255), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_all_day = Column(Boolean, default=False)
    is_fixed = Column(Boolean, default=True) # True = locked calendar event, False = floating task block
    
    event_category = Column(String(32), default="meeting") # meeting, focus, personal, ai_starter_task
    cognitive_weight = Column(Numeric(3, 2), default=1.0) # 1.5 high energy, 1.0 standard, 0.6 light, 1.2 deep focus
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
