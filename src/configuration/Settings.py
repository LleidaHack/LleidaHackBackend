from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    secret_key: str = Field(default="secret", description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    expire_time: int = Field(default=15, description="JWT expiration time in minutes")
    service_token: str = Field(default="HOLA", description="Service authentication token")


class DatabaseSettings(BaseSettings):
    url: str = Field(..., description="Database connection URL")


class MailClientSettings(BaseSettings):
    url: str = Field(..., description="Mail service URL")


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
    front_url: str = Field(default="https://frontend.integration.lleidahack.dev/hackeps")
    back_url: str = Field(default="http://localhost:8000/", alias="BACK_URL")
    static_folder: str = Field(default="static")
    contact_mail: str = Field(default="contacte@lleidahack.dev")
    local: bool = Field(default=True, alias="LOCAL")
    
    # Environment
    env: str = Field(default="integration", alias="ENV")
    
    # Nested settings
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    database: DatabaseSettings
    clients: ClientsSettings
    
    def __init__(self, **kwargs):
        # Handle environment-specific database URLs
        env = kwargs.get('env') or 'integration'
        
        if env == 'integration':
            # Integration environment database
            postgres_password = kwargs.get('integration_postgres_password', 'testpass123')
            default_db_url = f"postgresql://lleidahack_user:{postgres_password}@db-integration:5432/lleidahack_integration"
            kwargs.setdefault('database', {'url': default_db_url})
            kwargs.setdefault('clients', {
                'mail_client': {'url': 'http://mail-backend-integration:8001/'}
            })
        else:
            # Main environment database
            default_db_url = "postgresql+psycopg2://ton:kSw3nMZF5LC3A248@89.117.56.116:5432/ton_test1"
            kwargs.setdefault('database', {'url': default_db_url})
            kwargs.setdefault('clients', {
                'mail_client': {'url': 'http://mail:8000/'}
            })
            
        super().__init__(**kwargs)


# Global settings instance
settings = Settings()