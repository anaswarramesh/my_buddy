from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.calendar import CalendarEvent
from app.models.user import User

class CalendarService:
    @staticmethod
    def get_events_for_range(
        db: Session,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> List[CalendarEvent]:
        start_dt = datetime.combine(start_date, time(0, 0, 0))
        end_dt = datetime.combine(end_date, time(23, 59, 59))
        
        return db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_dt,
            CalendarEvent.start_time <= end_dt
        ).order_by(CalendarEvent.start_time.asc()).all()

    @staticmethod
    def seed_demo_calendar(db: Session, user_id: str):
        """
        Seeds a realistic 7-day calendar with a mix of heavy meeting days (Orange/Red)
        and light focus days (Green/Yellow) to demonstrate smart scheduling.
        """
        # Clear existing demo events
        db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).delete()
        
        today = date.today()
        
        events_to_seed = [
            # Today: Moderate Load (2 meetings)
            CalendarEvent(
                user_id=user_id,
                title="Daily Product Sync",
                start_time=datetime.combine(today, time(9, 30)),
                end_time=datetime.combine(today, time(10, 15)),
                event_category="meeting",
                cognitive_weight=1.0,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="Engineering Architecture Review",
                start_time=datetime.combine(today, time(14, 0)),
                end_time=datetime.combine(today, time(15, 30)),
                event_category="meeting",
                cognitive_weight=1.5,
                is_fixed=True
            ),

            # Tomorrow: Heavy / Overloaded Day (4 meetings back-to-back)
            CalendarEvent(
                user_id=user_id,
                title="Client Quarterly Review",
                start_time=datetime.combine(today + timedelta(days=1), time(9, 0)),
                end_time=datetime.combine(today + timedelta(days=1), time(10, 30)),
                event_category="meeting",
                cognitive_weight=1.5,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="Hiring & Interview: Staff Architect",
                start_time=datetime.combine(today + timedelta(days=1), time(11, 0)),
                end_time=datetime.combine(today + timedelta(days=1), time(12, 0)),
                event_category="meeting",
                cognitive_weight=1.2,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="All-Hands Company Meeting",
                start_time=datetime.combine(today + timedelta(days=1), time(13, 30)),
                end_time=datetime.combine(today + timedelta(days=1), time(15, 0)),
                event_category="meeting",
                cognitive_weight=1.0,
                is_fixed=True
            ),
            CalendarEvent(
                user_id=user_id,
                title="Vendor Contract Negotiation",
                start_time=datetime.combine(today + timedelta(days=1), time(16, 0)),
                end_time=datetime.combine(today + timedelta(days=1), time(17, 30)),
                event_category="meeting",
                cognitive_weight=1.5,
                is_fixed=True
            ),

            # Day 2: Green Focus Day (Only 1 short morning sync)
            CalendarEvent(
                user_id=user_id,
                title="Quick 15-min Standup",
                start_time=datetime.combine(today + timedelta(days=2), time(9, 15)),
                end_time=datetime.combine(today + timedelta(days=2), time(9, 30)),
                event_category="meeting",
                cognitive_weight=0.8,
                is_fixed=True
            ),

            # Day 3: Light Day
            CalendarEvent(
                user_id=user_id,
                title="Design System Review",
                start_time=datetime.combine(today + timedelta(days=3), time(11, 0)),
                end_time=datetime.combine(today + timedelta(days=3), time(12, 0)),
                event_category="meeting",
                cognitive_weight=1.0,
                is_fixed=True
            ),
        ]

        db.add_all(events_to_seed)
        db.commit()
