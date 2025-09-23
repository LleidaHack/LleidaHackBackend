from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class SecuritySettings(BaseSettings):
    secret_key: str = Field(
        default="secret", 
        description="JWT secret key",
        env="SECURITY__SECRET_KEY"
    )
    algorithm: str = Field(
        default="HS256", 
        description="JWT algorithm",
        env="SECURITY__ALGORITHM"
    )
    expire_time: int = Field(
        default=15, 
        description="JWT expiration time in minutes",
        env="SECURITY__EXPIRE_TIME"
    )
    service_token: str = Field(
        default="HOLA", 
        description="Service authentication token",
        env="SECURITY__SERVICE_TOKEN"
    )


class DatabaseSettings(BaseSettings):
    url: str = Field(
        ..., 
        description="Database connection URL",
        env="DATABASE__URL"
    )


class MailClientSettings(BaseSettings):
    url: str = Field(
        ..., 
        description="Mail service URL",
        env="CLIENTS__MAIL_CLIENT__URL"
    )


class ClientsSettings(BaseSettings):
    mail_client: MailClientSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow"
    )
    
    # General settings
    front_url: str = Field(
        default="https://frontend.integration.lleidahack.dev/hackeps",
        description="Frontend URL",
        env="FRONT_URL"
    )
    back_url: str = Field(
        default="http://localhost:8000/", 
        description="Backend URL",
        env="BACK_URL"
    )
    static_folder: str = Field(
        default="static",
        description="Static files folder path",
        env="STATIC_FOLDER"
    )
    contact_mail: str = Field(
        default="contacte@lleidahack.dev",
        description="Contact email address",
        env="CONTACT_MAIL"
    )
    local: bool = Field(
        default=True,
        description="Local development mode",
        env="LOCAL"
    )
    
    # Environment
    env: str = Field(
        default="main", 
        description="Environment name (main/integration)",
        env="ENV"
    )
    
    # Nested settings
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    database: DatabaseSettings
    clients: ClientsSettings
    
    def __init__(self, **kwargs):
        # Handle environment-specific defaults
        env = os.environ.get('ENV', 'main')
        
        if env == 'integration':
            # Integration environment defaults
            postgres_password = os.environ.get('INTEGRATION_POSTGRES_PASSWORD', 'testpass123')
            kwargs.setdefault('database', {
                'url': f"postgresql://lleidahack_user:{postgres_password}@db-integration:5432/lleidahack_integration"
            })
            kwargs.setdefault('clients', {
                'mail_client': {'url': 'http://mail-backend-integration:8001/'}
            })
        else:
            # Main environment defaults - use env vars for sensitive data
            db_url = os.environ.get('DATABASE__URL')
            if not db_url:
                raise ValueError("DATABASE__URL environment variable is required for production")
            
            kwargs.setdefault('database', {'url': db_url})
            kwargs.setdefault('clients', {
                'mail_client': {'url': os.environ.get('CLIENTS__MAIL_CLIENT__URL', 'http://mail:8000/')}
            })
            
        super().__init__(**kwargs)


# Global settings instance
settings = Settings()