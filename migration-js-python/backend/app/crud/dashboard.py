from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Dict, Any
from datetime import datetime, timedelta

from app.models.transaction import Transaction


class DashboardCRUD:
    def get_dashboard_data(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data with optimized queries"""
        now = datetime.utcnow()
        
        # Current month stats (single query)
        monthly_stats = self._get_monthly_stats_optimized(db, user_id, now.year, now.month)
        
        # Recent transactions (limited)
        recent_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(desc(Transaction.created_at)).limit(5).all()
        
        # Top merchants (aggregated)
        top_merchants = db.query(
            Transaction.merchant,
            func.sum(Transaction.amount).label('total_spent'),
            func.count(Transaction.id).label('transaction_count')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.merchant.isnot(None),
            Transaction.transaction_type == 'expense'
        ).group_by(Transaction.merchant).order_by(desc('total_spent')).limit(5).all()
        
        return {
            "monthly_stats": monthly_stats,
            "recent_transactions": [t.to_dict() for t in recent_transactions],
            "top_merchants": [
                {
                    "merchant": m.merchant,
                    "total_spent": float(m.total_spent),
                    "transaction_count": m.transaction_count
                }
                for m in top_merchants
            ]
        }
    
    def _get_monthly_stats_optimized(self, db: Session, user_id: str, year: int, month: int) -> Dict[str, Any]:
        """Optimized monthly stats using database aggregation"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Single query for main stats
        stats = db.query(
            func.sum(case((Transaction.transaction_type == 'expense', Transaction.amount), else_=0)).label('total_spent'),
            func.sum(case((Transaction.transaction_type == 'income', Transaction.amount), else_=0)).label('total_income'),
            func.count(Transaction.id).label('transaction_count'),
            func.avg(case((Transaction.transaction_type == 'expense', Transaction.amount))).label('avg_expense')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date < end_date
        ).first()
        
        # Category breakdown
        categories = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.transaction_type == 'expense'
        ).group_by(Transaction.category).all()
        
        by_category = {}
        for cat in categories:
            category_name = cat.category or "Uncategorized"
            by_category[category_name] = {
                "total": float(cat.total),
                "count": cat.count
            }
        
        return {
            "total_spent": float(stats.total_spent or 0),
            "total_income": float(stats.total_income or 0),
            "transaction_count": stats.transaction_count or 0,
            "by_category": by_category,
            "period": f"{year}-{month:02d}",
            "average_transaction": float(stats.avg_expense or 0)
        }


dashboard_crud = DashboardCRUD()