from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)  # This stays String
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String)
    last_name = Column(String)
    avatar_url = Column(String)
    
    # Settings
    currency = Column(String, default="RON")  # Changed from USD to RON
    timezone = Column(String, default="UTC")
    preferences = Column(JSON, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships - removed to avoid circular dependency issues
    # transactions = relationship("Transaction", back_populates="user")
    # budget_categories = relationship("BudgetCategory", back_populates="user")
    # financial_goals = relationship("FinancialGoal", back_populates="user")
    # recurring_transactions = relationship("RecurringTransaction", back_populates="user")
    # subscription = relationship("Subscription", back_populates="user", uselist=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "clerk_user_id": self.clerk_user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "avatar_url": self.avatar_url,
            "currency": self.currency,
            "timezone": self.timezone,
            "preferences": self.preferences,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "onboarding_completed": self.onboarding_completed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
