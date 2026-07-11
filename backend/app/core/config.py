from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str
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


settings = Settings()
