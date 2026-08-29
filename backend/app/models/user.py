import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    timezone = Column(String(64), default="UTC")
    coaching_style = Column(String(32), default="proactive_challenger") # gentle, proactive_challenger, analytical
    max_density_threshold = Column(Numeric(3, 2), default=0.75)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
