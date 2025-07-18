from typing import Any, Optional, Dict
from fastapi import Response
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standardized API response format"""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[Dict[str, Any]] = None


def success_response(data: Any = None, message: str = None) -> APIResponse:
    """Create a success response"""
    return APIResponse(success=True, data=data, message=message)


def error_response(message: str, errors: Dict[str, Any] = None) -> APIResponse:
    """Create an error response"""
    return APIResponse(success=False, message=message, errors=errors)


def set_cors_headers(response: Response) -> None:
    """Set CORS headers for API responses"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"


def set_cache_headers(response: Response, max_age: int = 0) -> None:
    """Set cache control headers"""
    if max_age > 0:
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"