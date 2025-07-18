from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.crud.dashboard import dashboard_crud

router = APIRouter()


@router.get("/")
async def get_dashboard_data(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get optimized dashboard data with single query"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    dashboard_data = dashboard_crud.get_dashboard_data(db, user_id)
    return dashboard_data


@router.options("/")
async def dashboard_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}