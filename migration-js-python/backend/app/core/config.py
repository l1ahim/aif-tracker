from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database - Updated to handle both local and Docker environments
    DATABASE_URL: str = "postgresql://aif_tracker:password123@localhost:5432/aif_tracker"
    
    # Authentication
    CLERK_SECRET_KEY: str = ""
    JWT_SECRET_KEY: str = "dev-secret-key"
    JWT_ALGORITHM: str = "HS256"
    
    # External APIs
    GEMINI_API_KEY: str = ""
    AZURE_AI_ENDPOINT: str = ""
    AZURE_AI_KEY: str = ""
    AZURE_FORM_RECOGNIZER_ENDPOINT: str = ""  # Added missing field
    AZURE_FORM_RECOGNIZER_KEY: str = ""       # Added missing field
    STRIPE_SECRET_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    
    # Redis (even though we removed Celery, keep for future use)
    REDIS_URL: str = "redis://localhost:6379"  # Added missing field
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # File uploads
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # AI settings
    GEMINI_MODEL: str = "gemini-pro-vision"
    PREFERRED_AI_PROVIDER: str = "auto"
    
    # Development
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields instead of raising error

    @property
    def has_gemini_config(self) -> bool:
        return bool(self.GEMINI_API_KEY)
    
    @property
    def has_azure_config(self) -> bool:
        return bool(self.AZURE_AI_KEY and self.AZURE_AI_ENDPOINT)
    
    @property
    def active_ai_provider(self) -> str:
        if self.PREFERRED_AI_PROVIDER == "gemini" and self.has_gemini_config:
            return "gemini"
        elif self.PREFERRED_AI_PROVIDER == "azure" and self.has_azure_config:
            return "azure"
        elif self.PREFERRED_AI_PROVIDER == "auto":
            if self.has_gemini_config:
                return "gemini"
            elif self.has_azure_config:
                return "azure"
        return "none"
    
    @property
    def database_url_for_context(self) -> str:
        """Get database URL based on runtime context"""
        import os
        
        # If running in Docker, use the service name
        if os.getenv('DOCKER_ENV') == 'true':
            return self.DATABASE_URL.replace('localhost', 'postgres')
        
        # If DATABASE_URL is already set with postgres hostname, use as-is
        if 'postgres:5432' in self.DATABASE_URL:
            return self.DATABASE_URL
            
        return self.DATABASE_URL


settings = Settings()
