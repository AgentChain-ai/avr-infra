"""
Configuration management for Akash Institute Outreach System
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Akash Institute Outreach System"
    debug: bool = Field(default=False, alias="AKASH_DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="AKASH_HOST")
    port: int = Field(default=8000, alias="AKASH_API_PORT")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./akash_outreach.db",
        alias="AKASH_DATABASE_URL"
    )
    
    # Authentication
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    
    # AI Services
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    
    # AVR Integration
    avr_core_url: str = Field(default="http://localhost:5001", alias="AVR_CORE_URL")
    avr_ami_url: str = Field(default="http://localhost:6006", alias="AVR_AMI_URL")
    
    # File Upload
    upload_dir: str = Field(default="./data/uploads", alias="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, alias="MAX_FILE_SIZE")  # 10MB
    
    # Calling Configuration
    default_call_extension: str = Field(default="5001", alias="DEFAULT_CALL_EXTENSION")
    max_concurrent_calls: int = Field(default=5, alias="MAX_CONCURRENT_CALLS")
    call_timeout: int = Field(default=300, alias="CALL_TIMEOUT")  # 5 minutes
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    class Config:
        env_file = [".env", "../.env"]  # Look for local .env first, then parent
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def get_database_url() -> str:
    """Get database URL with absolute path"""
    if settings.database_url.startswith("sqlite:///./"):
        # Convert relative path to absolute
        db_path = settings.database_url.replace("sqlite:///./", "")
        abs_path = os.path.abspath(db_path)
        return f"sqlite:///{abs_path}"
    return settings.database_url


# Environment validation
def validate_environment():
    """Validate required environment variables"""
    errors = []
    
    if not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is required for AI services")
    
    if settings.admin_password == "admin123":
        print("⚠️  WARNING: Using default admin password. Change ADMIN_PASSWORD in production!")
    
    if settings.secret_key == "your-secret-key-change-in-production":
        print("⚠️  WARNING: Using default secret key. Change SECRET_KEY in production!")
    
    if errors:
        raise ValueError(f"Environment validation failed: {', '.join(errors)}")
    
    return True


if __name__ == "__main__":
    # Test configuration loading
    print("=== Akash Outreach Configuration ===")
    print(f"App Name: {settings.app_name}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Database URL: {get_database_url()}")
    print(f"API Port: {settings.port}")
    print(f"OpenAI API Key: {'✅ Set' if settings.openai_api_key else '❌ Missing'}")
    print(f"AVR Core URL: {settings.avr_core_url}")
    print(f"Upload Directory: {settings.upload_dir}")
    
    try:
        validate_environment()
        print("✅ Environment validation passed")
    except ValueError as e:
        print(f"❌ Environment validation failed: {e}")
