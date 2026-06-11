from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str
    DATABASE_URL: str
    ENCRYPTION_KEY: str

    REDIS_URL: str

    SLEEPER_REST_BASE: str = "https://api.sleeper.app/v1"
    SLEEPER_GRAPHQL_URL: str = "https://sleeper.com/graphql"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()