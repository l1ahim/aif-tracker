#!/usr/bin/env python3
"""
Script to initialize database and run migrations
"""
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_db():
    """Initialize database with tables"""
    try:
        from app.core.database import engine, Base
        from app.models import *  # Import all models
        
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_db()
    if not success:
        sys.exit(1)
