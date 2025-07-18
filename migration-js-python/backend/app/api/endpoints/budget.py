from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.transaction import BudgetCategory
from app.schemas.transaction import BudgetCategoryCreate, BudgetCategoryResponse

router = APIRouter()


@router.post("/categories", response_model=BudgetCategoryResponse)
async def create_budget_category(
    category: BudgetCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget category"""
    db_category = BudgetCategory(
        user_id=current_user.id,
        **category.dict()
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    response = db_category.to_dict()
    response['current_spending'] = db_category.get_current_spending(db)
    return response


@router.get("/categories", response_model=List[BudgetCategoryResponse])
async def get_budget_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's budget categories"""
    categories = db.query(BudgetCategory).filter(
        BudgetCategory.user_id == current_user.id,
        BudgetCategory.is_active == True
    ).all()
    
    result = []
    for category in categories:
        cat_dict = category.to_dict()
        cat_dict['current_spending'] = category.get_current_spending(db)
        result.append(cat_dict)
    
    return result


@router.get("/alerts")
async def get_budget_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get budget alerts for user"""
    categories = db.query(BudgetCategory).filter(
        BudgetCategory.user_id == current_user.id,
        BudgetCategory.is_active == True
    ).all()
    
    alerts = []
    for category in categories:
        current_spending = category.get_current_spending(db)
        
        if category.is_over_budget(db):
            alerts.append({
                "type": "over_budget",
                "category": category.name,
                "current": current_spending,
                "limit": category.budget_limit,
                "percentage": (current_spending / category.budget_limit) * 100
            })
        elif category.is_near_budget_limit(db):
            alerts.append({
                "type": "approaching_limit",
                "category": category.name,
                "current": current_spending,
                "limit": category.budget_limit,
                "percentage": (current_spending / category.budget_limit) * 100
            })
    
    return {"alerts": alerts}
