from pydantic_settings import BaseSettings, SettingsConfigDict
from app.integrations.sleeper.config import SleeperConfig

class Settings(BaseSettings):
    DATABASE_URL: str
    sleeper: SleeperConfig = SleeperConfig()
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()