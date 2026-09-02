from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.calendar import CalendarEvent
from app.models.density import DailyDensitySnapshot
from app.services.density_service import DensityService
from app.services.calendar_service import CalendarService

class SchedulerService:
    @staticmethod
    def auto_schedule_task(
        db: Session,
        user_id: str,
        task: Task,
        search_days: int = 7,
        target_date: Optional[date] = None
    ) -> Optional[CalendarEvent]:
        """
        Finds the optimal low-density 'Green Day' focus window for the task,
        creates a CalendarEvent block, and binds the task to it.
        If target_date is supplied, schedules directly into that specific day.
        """
        today = date.today()
        dates_to_check = [target_date] if target_date else [today + timedelta(days=offset) for offset in range(search_days)]
        
        # Scan days
        for cur_date in dates_to_check:
            events = CalendarService.get_events_for_range(db, user_id, cur_date, cur_date)
            density_res = DensityService.calculate_day_density(cur_date, events)

            # Rule: Don't schedule into overloaded days unless explicitly requested
            if not target_date and density_res.density_score > 0.70:
                continue

            # Look for an available focus window with sufficient duration
            for window in density_res.available_focus_windows:
                if window.duration_minutes >= task.estimated_minutes:
                    # Calculate start and end datetime
                    h_start, m_start = map(int, window.start_time.split(":"))
                    start_dt = datetime.combine(target_date, time(h_start, m_start))
                    end_dt = start_dt + timedelta(minutes=task.estimated_minutes)

                    # Create the calendar event
                    cal_event = CalendarEvent(
                        user_id=user_id,
                        title=f"⚡ {task.title}",
                        description=f"AI-Scheduled Starter Action (Friction: {task.friction_level})",
                        start_time=start_dt,
                        end_time=end_dt,
                        is_fixed=False, # Floating task event
                        event_category="ai_starter_task",
                        cognitive_weight=0.9
                    )
                    db.add(cal_event)
                    db.flush()

                    # Update task
                    task.is_scheduled = True
                    task.scheduled_start = start_dt
                    task.scheduled_end = end_dt
                    task.status = "scheduled"
                    task.linked_event_id = cal_event.id
                    db.commit()
                    db.refresh(task)

                    return cal_event

        return None
