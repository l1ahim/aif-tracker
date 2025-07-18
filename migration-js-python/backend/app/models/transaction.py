from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, Index, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(Text)
    category = Column(String)
    merchant = Column(String)
    date = Column(DateTime)  # Transaction/receipt date
    created_at = Column(DateTime, default=datetime.utcnow)  # When added to system
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Essential fields only
    receipt_hash = Column(String, index=True)
    ai_confidence = Column(Float)
    processing_status = Column(String, default="pending")
    transaction_type = Column(String, default="expense")
    manually_verified = Column(Boolean, default=False)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('ix_transactions_user_date', 'user_id', 'date'),
        Index('ix_transactions_user_category', 'user_id', 'category'),
        Index('ix_transactions_user_merchant', 'user_id', 'merchant'),
        Index('ix_transactions_receipt_hash', 'receipt_hash'),
        Index('ix_transactions_user_type_date', 'user_id', 'transaction_type', 'date'),
    )

    # Relationships - simplified to avoid join issues
    # user = relationship("User", foreign_keys=[user_id], primaryjoin="Transaction.user_id==User.clerk_user_id")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "amount": float(self.amount) if self.amount else 0.0,
            "description": self.description,
            "category": self.category,
            "merchant": self.merchant,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "ai_confidence": self.ai_confidence,
            "processing_status": self.processing_status,
            "transaction_type": self.transaction_type or "expense",
            "manually_verified": self.manually_verified,
        }


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    budget_limit = Column(Float)
    color = Column(String)
    icon = Column(String)
    description = Column(Text)
    
    # Budget period settings
    period_type = Column(String, default="monthly")  # monthly, weekly, yearly
    is_active = Column(Boolean, default=True)
    
    # Alert settings
    alert_threshold = Column(Float, default=0.8)  # Alert at 80% of budget
    email_alerts = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - removed to avoid join issues
    # user = relationship("User", foreign_keys=[user_id], primaryjoin="BudgetCategory.user_id==User.clerk_user_id")
    # transactions = relationship("Transaction", back_populates="budget_category")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "budget_limit": self.budget_limit,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "period_type": self.period_type,
            "is_active": self.is_active,
            "alert_threshold": self.alert_threshold,
            "email_alerts": self.email_alerts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def get_current_spending(self, db_session):
        """Get current period spending for this category"""
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        now = datetime.utcnow()
        if self.period_type == "monthly":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.period_type == "weekly":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # yearly
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total = db_session.query(func.sum(Transaction.amount)).filter(
            Transaction.budget_category_id == self.id,
            Transaction.date >= start_date,
            Transaction.transaction_type == "expense"
        ).scalar() or 0.0
        
        return total

    def is_over_budget(self, db_session):
        """Check if current spending exceeds budget"""
        if not self.budget_limit:
            return False
        return self.get_current_spending(db_session) > self.budget_limit

    def is_near_budget_limit(self, db_session):
        """Check if spending is near the alert threshold"""
        if not self.budget_limit:
            return False
        current_spending = self.get_current_spending(db_session)
        return current_spending >= (self.budget_limit * self.alert_threshold)


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # String to match clerk_user_id
    name = Column(String, nullable=False)  # e.g., "Save for Vacation"
    description = Column(Text)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime)
    
    # Goal type and category
    goal_type = Column(String, default="savings")  # savings, debt_reduction, expense_reduction
    category = Column(String)  # vacation, emergency_fund, new_laptop
    
    # Visual and tracking
    color = Column(String)
    icon = Column(String)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - removed to avoid join issues
    # user = relationship("User", foreign_keys=[user_id], primaryjoin="FinancialGoal.user_id==User.clerk_user_id")

    def to_dict(self):
        progress_percentage = (self.current_amount / self.target_amount * 100) if self.target_amount > 0 else 0
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "progress_percentage": min(progress_percentage, 100),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "goal_type": self.goal_type,
            "category": self.category,
            "color": self.color,
            "icon": self.icon,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # String to match clerk_user_id
    
    # Transaction template
    amount = Column(Float, nullable=False)
    description = Column(Text)
    category = Column(String)
    merchant = Column(String)
    payment_method = Column(String)
    
    # Recurrence settings
    frequency = Column(String, nullable=False)  # daily, weekly, monthly, yearly
    interval_count = Column(Integer, default=1)  # every N periods
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)  # Optional end date
    
    # Status
    is_active = Column(Boolean, default=True)
    next_due_date = Column(DateTime)
    last_created_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships - removed to avoid join issues  
    # user = relationship("User", foreign_keys=[user_id], primaryjoin="RecurringTransaction.user_id==User.clerk_user_id")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "amount": self.amount,
            "description": self.description,
            "category": self.category,
            "merchant": self.merchant,
            "payment_method": self.payment_method,
            "frequency": self.frequency,
            "interval_count": self.interval_count,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "created_at": self.created_at.isoformat(),
        }
