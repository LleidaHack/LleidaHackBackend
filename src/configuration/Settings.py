import os
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SECURITY__",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )
    secret_key: str = Field(
        min_length=32, description="JWT secret key", env="SECURITY__SECRET_KEY"
    )
    algorithm: str = Field(
        default="HS256", description="JWT algorithm", env="SECURITY__ALGORITHM"
    )
    expire_time: int = Field(
        default=15,
        description="JWT expiration time in minutes",
        env="SECURITY__EXPIRE_TIME",
    )
    service_token: str = Field(
        min_length=32,
        description="Service authentication token",
        env="SECURITY__SERVICE_TOKEN",
    )

    @field_validator("secret_key", "service_token")
    @classmethod
    def validate_secret(cls, value: str):
        if not value.strip() or value.lower().startswith(
            ("your-", "tu-", "change", "${")
        ):
            raise ValueError("Configure a unique secret with at least 32 characters")
        return value

    @model_validator(mode="after")
    def independent_secrets(self):
        if self.secret_key == self.service_token:
            raise ValueError("JWT and service secrets must be independent")
        return self


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )
    url: str = Field(..., description="Database connection URL", env="DATABASE__URL")


class MailClientSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )
    url: str = Field(
        ..., description="Mail service URL", env="CLIENTS__MAIL_CLIENT__URL"
    )


class ClientsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )
    mail_client: MailClientSettings


class RateLimitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT__", extra="ignore")
    enabled: bool = True
    redis_url: str = "redis://127.0.0.1:6379/0"
    prefix: str = "lleidahack:limits"
    requests_per_minute: int = Field(default=300, ge=1)
    burst_per_second: int = Field(default=30, ge=1)
    login_per_minute: int = Field(default=20, ge=1)
    login_per_account: int = Field(default=10, ge=1)
    signup_per_hour: int = Field(default=10, ge=1)
    mail_per_hour: int = Field(default=20, ge=1)
    mail_per_recipient: int = Field(default=3, ge=1)
    mail_total_per_hour: int = Field(default=300, ge=1)
    max_body_bytes: int = Field(default=3145728, ge=1024)
    body_timeout_seconds: float = Field(default=10, gt=0)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )

    cors_origins: list[str] = Field(default_factory=list)

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, values):
        for value in values:
            parsed = urlsplit(value)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
            ):
                raise ValueError(
                    "CORS origins must be explicit HTTP(S) origins without paths"
                )
        return values

    # General settings
    front_url: str = Field(
        default="https://frontend.integration.lleidahack.dev/hackeps",
        description="Frontend URL",
        env="FRONT_URL",
    )
    back_url: str = Field(
        default="http://localhost:8000/", description="Backend URL", env="BACK_URL"
    )
    static_folder: str = Field(
        default="static", description="Static files folder path", env="STATIC_FOLDER"
    )
    contact_mail: str = Field(
        default="contacte@lleidahack.dev",
        description="Contact email address",
        env="CONTACT_MAIL",
    )
    local: bool = Field(
        default=False, description="Local development mode", env="LOCAL"
    )

    # Environment
    env: str = Field(
        default="main", description="Environment name (main/integration)", env="ENV"
    )

    # Nested settings
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    database: DatabaseSettings
    clients: ClientsSettings

    def __init__(self, **kwargs):
        # Handle environment-specific defaults
        env = os.environ.get("ENV", "main")

        if env == "integration":
            # Integration environment defaults
            db_url = os.environ.get("DATABASE__URL")
            if not db_url:
                raise ValueError(
                    "DATABASE__URL is required for integration; no default password is allowed"
                )
            kwargs.setdefault("database", {"url": db_url})
            kwargs.setdefault(
                "clients",
                {"mail_client": {"url": "http://mail-backend-integration:8001/"}},
            )
        else:
            # Main environment defaults - use env vars for sensitive data
            db_url = os.environ.get("DATABASE__URL")
            if not db_url:
                raise ValueError(
                    "DATABASE__URL environment variable is required for production"
                )

            kwargs.setdefault("database", {"url": db_url})
            kwargs.setdefault(
                "clients",
                {
                    "mail_client": {
                        "url": os.environ.get(
                            "CLIENTS__MAIL_CLIENT__URL", "http://mail:8000/"
                        )
                    }
                },
            )

        super().__init__(**kwargs)


# Global settings instance
settings = Settings()
