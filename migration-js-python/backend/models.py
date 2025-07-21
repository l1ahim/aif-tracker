from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(Text)
    category = Column(String(100))
    merchant = Column(String(255))
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    receipt_hash = Column(String(255), index=True)
    ai_confidence = Column(Float)
    processing_status = Column(String(50), default='pending')
    transaction_type = Column(String(20), nullable=False, default='expense')
    manually_verified = Column(Boolean, default=False)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': str(self.id),  # Convert UUID to string for JSON serialization
            'user_id': self.user_id,
            'amount': self.amount,
            'description': self.description,
            'category': self.category,
            'merchant': self.merchant,
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'receipt_hash': self.receipt_hash,
            'ai_confidence': self.ai_confidence,
            'processing_status': self.processing_status,
            'transaction_type': self.transaction_type,
            'manually_verified': self.manually_verified
        }
