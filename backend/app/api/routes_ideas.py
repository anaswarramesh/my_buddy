from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.idea import Idea
from app.models.task import Task
from app.schemas.idea import IdeaResponse, IdeaCreate, IdeaDecompositionResponse
from app.schemas.task import TaskResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/ideas", tags=["Idea Backlog & Coaching"])

@router.get("", response_model=List[IdeaResponse])
def get_ideas(user_id: str = "default-user", db: Session = Depends(get_db)):
    return db.query(Idea).filter(Idea.user_id == user_id).order_by(Idea.created_at.desc()).all()

@router.get("/{idea_id}", response_model=IdeaResponse)
def get_idea(idea_id: str, db: Session = Depends(get_db)):
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea

@router.get("/{idea_id}/tasks", response_model=List[TaskResponse])
def get_tasks_for_idea(idea_id: str, db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.idea_id == idea_id).order_by(Task.sequence_order.asc()).all()

@router.post("/{idea_id}/decompose", response_model=IdeaDecompositionResponse)
async def decompose_idea_endpoint(idea_id: str, db: Session = Depends(get_db)):
    """
    Triggers Prompt B on demand to decompose/re-decompose an idea into actionable micro-steps.
    """
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    tasks = await LLMService.decompose_idea(
        idea_title=idea.title,
        idea_summary=idea.summary or idea.raw_transcript,
        coaching_verdict=idea.coaching_verdict,
        primary_obstacle=idea.primary_obstacle
    )

    # Delete old tasks if any
    db.query(Task).filter(Task.idea_id == idea_id).delete()

    first_step_title = ""
    for t in tasks:
        task_db = Task(
            user_id=idea.user_id,
            idea_id=idea.id,
            title=t.title,
            description=t.description,
            is_starter_step=t.is_starter_step,
            sequence_order=t.sequence_order,
            estimated_minutes=t.estimated_minutes,
            friction_level=t.friction_level,
            energy_requirement=t.energy_requirement,
            priority=t.priority
        )
        if t.is_starter_step:
            first_step_title = t.title
        db.add(task_db)

    db.commit()

    return IdeaDecompositionResponse(
        idea_id=idea_id,
        tasks_generated=len(tasks),
        starter_step_title=first_step_title or tasks[0].title,
        coaching_message="Generated low-friction starter actions. Ready to auto-schedule into your lowest-density day."
    )
