from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class FantasyCalcConfig(BaseSettings):
    base_url: str = "https://api.fantasycalc.com"

    model_config = SettingsConfigDict(
        env_prefix="FANTASY_CALC_",
    )
