from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def check_database_health():
    """Check database connectivity"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "message": f"Database error: {str(e)}"}


async def check_ai_services_health():
    """Check AI services configuration"""
    services = {
        "gemini": settings.has_gemini_config,
        "azure": settings.has_azure_config
    }
    
    active_provider = settings.active_ai_provider
    
    if active_provider == "none":
        return {
            "status": "warning",
            "message": "No AI provider configured - receipt scanning will use fallback",
            "services": services
        }
    
    return {
        "status": "healthy",
        "message": f"AI provider '{active_provider}' is configured",
        "active_provider": active_provider,
        "services": services
    }


async def get_system_health():
    """Get comprehensive system health status"""
    db_health = await check_database_health()
    ai_health = await check_ai_services_health()
    
    overall_status = "healthy"
    if db_health["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif ai_health["status"] == "warning":
        overall_status = "warning"
    
    return {
        "status": overall_status,
        "database": db_health,
        "ai_services": ai_health,
        "environment": "development" if settings.DEBUG else "production"
    }