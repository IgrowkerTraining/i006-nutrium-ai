"""Application settings and configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    app_name: str = "Nutrium AI Service"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # OpenRouter Configuration
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # --- Database Configuration (ACTUALIZADO) ---
    # Leemos las variables desglosadas que envía Docker
    db_host: str = "localhost"
    db_user: str = "nutrium_user"
    db_pass: str = "nutrium_password"
    db_name: str = "nutrium_db"
    db_port: int = 5432
    
    # Construimos la URL internamente
    @property
    def database_url(self) -> str:
        # Construimos la cadena de conexión para PostgreSQL
        return f"postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Opciones de base de datos
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # CORS Configuration
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Logging Configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()