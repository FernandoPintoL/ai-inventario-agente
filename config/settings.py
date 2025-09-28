import os
from typing import Optional
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment Configuration
    environment: str = "development"  # development, production
    port: int = 8080  # Default port for Railway
    host: str = "0.0.0.0"  # Listen on all interfaces for production

    # Claude Configuration
    claude_api_key: str
    claude_model: str = "claude-3-5-haiku-20241022"
    claude_demo_mode: bool = False
    claude_fallback_enabled: bool = True

    # Database Configuration
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # Server Configuration
    server_url: str = "http://localhost:8080"
    secret_key: str
    allowed_hosts: str = "localhost,127.0.0.1"

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Railway/Production specific
    railway_environment_name: Optional[str] = None
    railway_public_domain: Optional[str] = None

    @field_validator('claude_api_key')
    @classmethod
    def validate_claude_key(cls, v):
        if not v or v == "your_claude_api_key_here":
            raise ValueError("CLAUDE_API_KEY must be set")
        return v

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if not v or v == "your-secret-key-here":
            raise ValueError("SECRET_KEY must be set")
        return v

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def base_url(self) -> str:
        """Get the base URL for the application."""
        if self.railway_public_domain:
            return f"https://{self.railway_public_domain}"
        elif self.is_production:
            return f"https://production-domain.com"  # Replace with actual domain
        else:
            return f"http://localhost:{self.port}"

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins based on environment."""
        if self.is_production:
            origins = [self.base_url]
            if self.railway_public_domain:
                origins.append(f"https://{self.railway_public_domain}")
            return origins
        else:
            return [
                f"http://localhost:{self.port}",
                f"http://127.0.0.1:{self.port}",
                "http://localhost:3000",  # Common frontend dev port
                "http://localhost:5173",  # Vite dev server
            ]

    @property
    def database_pool_config(self) -> dict:
        """Get database pool configuration based on environment."""
        if self.is_production:
            return {
                "pool_size": self.db_pool_size * 2,  # More connections in production
                "max_overflow": self.db_max_overflow * 2,
                "pool_timeout": self.db_pool_timeout,
                "pool_recycle": 3600,  # Recycle connections every hour
            }
        else:
            return {
                "pool_size": self.db_pool_size,
                "max_overflow": self.db_max_overflow,
                "pool_timeout": self.db_pool_timeout,
            }

    class Config:
        env_file = ".env"
        case_sensitive = False


# Load settings with Railway environment detection
def load_settings() -> Settings:
    """Load settings with Railway-specific environment variables."""

    # Detect Railway environment
    if os.getenv("RAILWAY_ENVIRONMENT"):
        os.environ.setdefault("ENVIRONMENT", "production")
        os.environ.setdefault("HOST", "0.0.0.0")
        os.environ.setdefault("PORT", "8080")

        # Set Railway-specific variables
        if railway_env := os.getenv("RAILWAY_ENVIRONMENT_NAME"):
            os.environ.setdefault("RAILWAY_ENVIRONMENT_NAME", railway_env)

        if railway_domain := os.getenv("RAILWAY_PUBLIC_DOMAIN"):
            os.environ.setdefault("RAILWAY_PUBLIC_DOMAIN", railway_domain)

    return Settings()


settings = load_settings()