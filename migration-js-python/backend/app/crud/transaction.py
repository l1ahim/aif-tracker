from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging

from app.models.transaction import Transaction, BudgetCategory

logger = logging.getLogger(__name__)


class TransactionCRUD:
    def create(self, db: Session, obj_in: dict, user_id: str) -> Transaction:
        """Create a new transaction"""
        try:
            db_obj = Transaction(
                user_id=user_id,
                **obj_in
            )
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            print(f"Transaction creation error: {e}")
            print(f"Transaction data: {obj_in}")
            print(f"User ID: {user_id}")
            raise

    def get(self, db: Session, transaction_id: UUID) -> Optional[Transaction]:
        """Get transaction by ID"""
        return db.query(Transaction).filter(Transaction.id == transaction_id).first()

    def get_by_user(
        self, 
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """Get user's transactions with optional filtering"""
        try:
            query = db.query(Transaction).filter(Transaction.user_id == user_id)
            
            if category:
                query = query.filter(Transaction.category == category)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error in get_by_user: {e}", exc_info=True)
            return []

    def get_monthly_stats(self, db: Session, user_id: str, year: int, month: int) -> dict:
        """Get monthly spending statistics with optimized query"""
        try:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            # Single optimized query with aggregation
            from sqlalchemy import case, func
            
            stats_query = db.query(
                func.sum(case((Transaction.transaction_type == 'expense', Transaction.amount), else_=0)).label('total_spent'),
                func.sum(case((Transaction.transaction_type == 'income', Transaction.amount), else_=0)).label('total_income'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(case((Transaction.transaction_type == 'expense', Transaction.amount))).label('avg_expense')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date < end_date
            ).first()
            
            # Category breakdown in separate optimized query
            category_query = db.query(
                Transaction.category,
                func.sum(Transaction.amount).label('total'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date < end_date,
                Transaction.transaction_type == 'expense'
            ).group_by(Transaction.category).all()
            
            # Process aggregated results
            total_spent = float(stats_query.total_spent or 0)
            total_income = float(stats_query.total_income or 0)
            transaction_count = stats_query.transaction_count or 0
            avg_transaction = float(stats_query.avg_expense or 0)
            
            # Build category breakdown
            by_category = {}
            for cat in category_query:
                category_name = cat.category or "Uncategorized"
                by_category[category_name] = {
                    "total": float(cat.total),
                    "count": cat.count
                }
            
            return {
                "total_spent": total_spent,
                "total_income": total_income,
                "transaction_count": transaction_count,
                "by_category": by_category,
                "period": f"{year}-{month:02d}",
                "average_transaction": avg_transaction
            }
            
        except Exception as e:
            logger.error(f"Error in get_monthly_stats: {e}", exc_info=True)
            return {
                "total_spent": 0.0,
                "total_income": 0.0,
                "transaction_count": 0,
                "by_category": {},
                "period": f"{year}-{month:02d}",
                "average_transaction": 0.0
            }

# Create instance
transaction_crud = TransactionCRUD()
