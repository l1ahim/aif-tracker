from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.transaction import FinancialGoal

router = APIRouter()

@router.post("/", response_model=dict)
async def create_financial_goal(
    goal_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new financial goal"""
    goal = FinancialGoal(
        user_id=current_user.id,
        name=goal_data["name"],
        description=goal_data.get("description"),
        target_amount=goal_data["target_amount"],
        target_date=goal_data.get("target_date"),
        goal_type=goal_data.get("goal_type", "savings"),
        category=goal_data.get("category"),
        color=goal_data.get("color", "#3B82F6"),
        icon=goal_data.get("icon", "💰")
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return goal.to_dict()

@router.get("/", response_model=List[dict])
async def get_financial_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's financial goals"""
    goals = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == current_user.id,
        FinancialGoal.is_active == True
    ).all()
    
    return [goal.to_dict() for goal in goals]

@router.put("/{goal_id}/progress")
async def update_goal_progress(
    goal_id: UUID,
    progress_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update goal progress (add/remove amount)"""
    goal = db.query(FinancialGoal).filter(
        FinancialGoal.id == goal_id,
        FinancialGoal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(404, "Goal not found")
    
    amount_change = progress_data.get("amount", 0)
    goal.current_amount += amount_change
    goal.current_amount = max(0, goal.current_amount)  # Don't go negative
    
    db.commit()
    return goal.to_dict()
