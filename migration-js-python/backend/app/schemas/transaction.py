from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    date: Optional[datetime] = None
    transaction_type: str = "expense"
    notes: Optional[str] = None
    tags: Optional[str] = None

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > 1000000:  # 1 million limit
            raise ValueError('Amount too large')
        return round(v, 2)  # Round to 2 decimal places
    
    @validator('description')
    def description_length(cls, v):
        if v and len(v) > 500:
            raise ValueError('Description too long (max 500 characters)')
        return v
    
    @validator('category')
    def category_length(cls, v):
        if v and len(v) > 50:
            raise ValueError('Category name too long (max 50 characters)')
        return v


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    date: Optional[datetime] = None
    manually_verified: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    ai_confidence: Optional[float] = None
    processing_status: str
    manually_verified: bool

    class Config:
        from_attributes = True


class BudgetCategoryCreate(BaseModel):
    name: str
    budget_limit: Optional[float] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    period_type: str = "monthly"


class BudgetCategoryResponse(BaseModel):
    id: UUID
    name: str
    budget_limit: Optional[float]
    color: Optional[str]
    icon: Optional[str]
    current_spending: Optional[float] = None
    
    class Config:
        from_attributes = True
