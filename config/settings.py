import os
from typing import Optional
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
    server_url: str = "http://localhost:8000"
    secret_key: str
    allowed_hosts: str = "localhost,127.0.0.1"

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

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

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()