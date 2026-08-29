import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    idea_id = Column(String(36), ForeignKey("ideas.id"), nullable=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Step Properties
    is_starter_step = Column(Boolean, default=False)
    sequence_order = Column(Integer, default=1)
    estimated_minutes = Column(Integer, default=30)
    friction_level = Column(String(32), default="easy") # micro, easy, medium, deep_work
    energy_requirement = Column(String(32), default="admin") # creative, deep_focus, admin, low_energy
    priority = Column(String(16), default="medium") # critical, high, medium, low
    
    # Scheduling State
    is_scheduled = Column(Boolean, default=False)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(String(32), default="pending") # pending, scheduled, in_progress, completed, floated
    
    linked_event_id = Column(String(36), ForeignKey("calendar_events.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    idea = relationship("Idea", back_populates="tasks")
    event = relationship("CalendarEvent", foreign_keys=[linked_event_id])
