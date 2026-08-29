import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Idea(Base):
    __tablename__ = "ideas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    raw_transcript = Column(Text, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    category = Column(String(64), default="business") # business, tech, creative, lifestyle
    
    # Feasibility & Coaching Analytics
    feasibility_score = Column(Integer, default=50) # 1 - 100
    impact_score = Column(Integer, default=50)      # 1 - 100
    friction_score = Column(Integer, default=50)    # 1 - 100
    coaching_verdict = Column(Text, nullable=True)
    primary_obstacle = Column(Text, nullable=True)
    nudge_strategy = Column(Text, nullable=True)
    
    status = Column(String(32), default="evaluating") # evaluating, active_coaching, in_progress, completed, parked
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="idea", cascade="all, delete-orphan")
