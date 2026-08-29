import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, DateTime, Numeric, Text, ForeignKey, UniqueConstraint
from app.database import Base

class DailyDensitySnapshot(Base):
    __tablename__ = "daily_density_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    total_committed_minutes = Column(Integer, default=0)
    meeting_count = Column(Integer, default=0)
    density_score = Column(Numeric(3, 2), default=0.0) # 0.00 to 1.00
    density_level = Column(String(16), default="light") # light, moderate, dense, overloaded
    available_focus_windows_json = Column(Text, default="[]") # JSON string of slot objects
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint('user_id', 'date', name='uq_user_density_date'),)
