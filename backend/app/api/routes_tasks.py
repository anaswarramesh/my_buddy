from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from app.database import get_db
from app.models.task import Task
from app.models.calendar import CalendarEvent
from app.schemas.task import TaskResponse, TaskCreate, TaskScheduleRequest
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/api/tasks", tags=["Actionable Tasks"])

@router.get("", response_model=List[TaskResponse])
def get_tasks(user_id: str = "default-user", db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.user_id == user_id).order_by(Task.created_at.desc()).all()

@router.post("", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        user_id=payload.user_id,
        idea_id=payload.idea_id,
        title=payload.title,
        description=payload.description,
        is_starter_step=payload.is_starter_step,
        sequence_order=payload.sequence_order,
        estimated_minutes=payload.estimated_minutes,
        friction_level=payload.friction_level,
        energy_requirement=payload.energy_requirement,
        priority=payload.priority,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/auto-schedule", response_model=TaskResponse)
def auto_schedule_task_endpoint(
    task_id: str,
    target_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Invokes Smart Scheduler to automatically match task with optimal Green/Light focus window.
    If target_date is supplied, schedules specifically for that date.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    event = SchedulerService.auto_schedule_task(db, task.user_id, task, target_date=target_date)
    if not event:
        raise HTTPException(status_code=400, detail="No suitable low-density focus window found.")

    return task

@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "completed"
    task.is_scheduled = False
    
    # Remove associated calendar event block so cognitive load drops immediately
    clean_title = task.title.replace("⚡", "").strip()
    db.query(CalendarEvent).filter(
        CalendarEvent.user_id == task.user_id,
        (CalendarEvent.title == clean_title) | (CalendarEvent.title == f"⚡ {clean_title}") | (CalendarEvent.title == task.title)
    ).delete(synchronize_session=False)

    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Remove associated calendar event block
    clean_title = task.title.replace("⚡", "").strip()
    db.query(CalendarEvent).filter(
        CalendarEvent.user_id == task.user_id,
        (CalendarEvent.title == clean_title) | (CalendarEvent.title == f"⚡ {clean_title}") | (CalendarEvent.title == task.title)
    ).delete(synchronize_session=False)

    db.delete(task)
    db.commit()
    return {"status": "deleted", "id": task_id}
