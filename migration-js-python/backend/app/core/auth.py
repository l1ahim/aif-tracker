from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import jwt  # This will now work with PyJWT package
import requests
import logging

from .config import settings
from .database import get_db
from ..models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Development mode check
DEVELOPMENT_MODE = not settings.CLERK_SECRET_KEY or settings.CLERK_SECRET_KEY == ""

def decode_jwt_token(token: str) -> dict:
    """Decode JWT token to extract user information"""
    try:
        # For development, we'll decode without verification
        # In production, you'd verify the signature with Clerk's public key
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise Exception("Invalid token format")

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Extract user ID from token or use development mode"""
    
    # Always use development mode for now
    return "dev-user-123"

async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from database"""
    
    # Auto-create user if doesn't exist
    user = db.query(User).filter(User.clerk_user_id == user_id).first()
    if not user:
        user = User(
            clerk_user_id=user_id,
            email="dev@example.com" if DEVELOPMENT_MODE else f"{user_id}@clerk.user",
            first_name="Development" if DEVELOPMENT_MODE else "User",
            last_name="User",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


# Simple auth for development/testing
async def get_current_user_id_simple(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Simple auth for testing - just return the token as user_id"""
    return credentials.credentials
