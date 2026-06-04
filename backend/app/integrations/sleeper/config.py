from pydantic_settings import BaseSettings

class SleeperConfig(BaseSettings):
    REST_BASE: str = "https://api.sleeper.app/v1"
    GRAPHQL_URL: str = "https://sleeper.com/graphql"

    RATE_LIMIT: int = 20
    RATE_PERIOD: float = 1.0

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }