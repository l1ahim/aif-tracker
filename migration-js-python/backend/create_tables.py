from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import uuid

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/aif_tracker')

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

def create_tables():
    """Create all tables in the database."""
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()
