from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager
from datetime import datetime
import logging

# Configure logging based on environment
import os
log_level = logging.DEBUG if os.getenv('DEBUG', 'false').lower() == 'true' else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress noisy logs in production
if log_level != logging.DEBUG:
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.api.main import api_router
from app.core.database import engine, Base
from app.models.user import User
from app.models.transaction import Transaction, BudgetCategory, FinancialGoal, RecurringTransaction
from app.models.subscription import Subscription


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    pass  # Removed verbose startup logging
    try:
        # Drop and recreate tables to fix column types
        if settings.DEBUG:
            Base.metadata.drop_all(bind=engine)
            pass  # Tables dropped
        
        Base.metadata.create_all(bind=engine)
        pass  # Tables created
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    yield
    # Shutdown
    pass  # Shutdown


app = FastAPI(
    title="AIF Tracker API",
    description="AI-powered financial tracking backend",
    version="1.0.0",
    lifespan=lifespan
)

# Security and performance middleware
from app.middleware.performance import PerformanceMiddleware

app.add_middleware(PerformanceMiddleware)

# CORS middleware - must be after performance middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"] if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "AIF Tracker API is running", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    from app.core.health import get_system_health
    
    try:
        health_status = await get_system_health()
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        if health_status["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=health_status)
        
        return health_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
