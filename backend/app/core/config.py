from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    ENVIRONMENT: str
    DEBUG_MODE: bool = False
    DATABASE_URL: str
    ENCRYPTION_KEY: str

    REDIS_URL: str
    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    SLEEPER_REST_BASE: str = "https://api.sleeper.app/v1"
    SLEEPER_REST_ALT: str = "https://api.sleeper.app"
    SLEEPER_GRAPHQL_URL: str = "https://sleeper.com/graphql"
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    EMAIL_FROM: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def include_debug_routes(self) -> bool:
        return self.DEBUG_MODE or (
            self.ENVIRONMENT.lower() != "production"
        )

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL.startswith("postgresql+"):
            return self.DATABASE_URL

        if self.DATABASE_URL.startswith("postgres://"):
            suffix = self.DATABASE_URL[len("postgres://"):]
            return f"postgresql+asyncpg://{suffix}"

        if self.DATABASE_URL.startswith("postgresql://"):
            suffix = self.DATABASE_URL[len("postgresql://"):]
            return f"postgresql+asyncpg://{suffix}"

        return self.DATABASE_URL

    @property
    def encryption_key_bytes(self) -> bytes:
        key = self.ENCRYPTION_KEY.encode()
        try:
            Fernet(key)
        except ValueError as exc:
            raise ValueError(
                "ENCRYPTION_KEY must be a valid Fernet key "
                "(32 url-safe base64-encoded bytes)."
            ) from exc
        return key


settings = Settings()
