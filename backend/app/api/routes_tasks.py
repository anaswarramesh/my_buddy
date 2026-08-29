from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.task import Task
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
def auto_schedule_task_endpoint(task_id: str, db: Session = Depends(get_db)):
    """
    Invokes Smart Scheduler to automatically match task with optimal Green/Light focus window.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    event = SchedulerService.auto_schedule_task(db, task.user_id, task)
    if not event:
        raise HTTPException(status_code=400, detail="No suitable low-density focus window found in the next 7 days.")

    return task

@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "completed"
    db.commit()
    db.refresh(task)
    return task
