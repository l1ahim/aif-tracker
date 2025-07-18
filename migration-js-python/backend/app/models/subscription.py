from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, unique=True)  # This stays String
    
    # Stripe integration
    stripe_customer_id = Column(String, unique=True)
    stripe_subscription_id = Column(String, unique=True)
    stripe_price_id = Column(String)
    
    # Subscription details
    plan_name = Column(String, nullable=False)  # free, premium, pro
    status = Column(String, nullable=False)  # active, canceled, past_due, incomplete
    amount = Column(Float)  # Monthly amount in cents
    currency = Column(String, default="USD")
    
    # Billing cycle
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    
    # Trial
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    
    # Status tracking
    is_active = Column(Boolean, default=False)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime)
    
    # Usage limits (for different plans)
    monthly_transaction_limit = Column(Integer, default=50)  # Free plan limit
    ai_scans_per_month = Column(Integer, default=10)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "plan_name": self.plan_name,
            "status": self.status,
            "amount": self.amount,
            "currency": self.currency,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "trial_start": self.trial_start.isoformat() if self.trial_start else None,
            "trial_end": self.trial_end.isoformat() if self.trial_end else None,
            "is_active": self.is_active,
            "cancel_at_period_end": self.cancel_at_period_end,
            "canceled_at": self.canceled_at.isoformat() if self.canceled_at else None,
            "monthly_transaction_limit": self.monthly_transaction_limit,
            "ai_scans_per_month": self.ai_scans_per_month,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @property
    def is_premium(self):
        return self.plan_name in ["premium", "pro"] and self.is_active

    @property
    def is_trial(self):
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end

    def can_use_ai_scan(self, current_usage):
        """Check if user can perform AI scan based on plan limits"""
        if self.is_premium:
            return True  # Unlimited for premium users
        return current_usage < self.ai_scans_per_month

    def can_add_transaction(self, current_count):
        """Check if user can add more transactions based on plan limits"""
        if self.is_premium:
            return True  # Unlimited for premium users
        return current_count < self.monthly_transaction_limit
