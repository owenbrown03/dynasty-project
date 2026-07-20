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
    ADP_CRAWL_ENABLED: bool = False
    ADP_CRAWL_SEASONS: str = "2026,2025"
    ADP_CACHE_TTL_SECONDS: int = 3600
    ADP_MIN_PLAYER_DRAFT_COUNT: int = 5
    ADP_MAX_DISCOVERY_DEPTH: int = 2
    ADP_MAX_NODES_PER_RUN: int = 50
    ADP_MAX_REQUESTS_PER_RUN: int = 250
    ADP_MAX_NEW_USERS_PER_RUN: int = 100
    ADP_MAX_NEW_LEAGUES_PER_RUN: int = 200
    ADP_MAX_NEW_DRAFTS_PER_RUN: int = 200
    ADP_MAX_RUNTIME_SECONDS: int = 300
    ADP_DISCOVERY_CONCURRENCY: int = 5
    ADP_INGEST_CONCURRENCY: int = 5
    ADP_REQUEST_DELAY_MS: int = 100
    ADP_PROCESSING_TIMEOUT_SECONDS: int = 900
    ADP_SNAPSHOT_MAX_AGE_SECONDS: int = 21600

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

    @property
    def adp_crawl_seasons(self) -> list[str]:
        return [
            season.strip()
            for season in self.ADP_CRAWL_SEASONS.split(",")
            if season.strip()
        ]


settings = Settings()
