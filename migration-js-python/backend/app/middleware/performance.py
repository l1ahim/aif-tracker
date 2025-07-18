import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track API performance"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add performance header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests (> 1 second)
        if process_time > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}s"
            )
        
        # Log all requests in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"{request.method} {request.url.path} "
                f"- {response.status_code} - {process_time:.3f}s"
            )
        
        return response