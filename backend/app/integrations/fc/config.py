from pydantic_settings import BaseSettings


class FantasyCalcConfig(BaseSettings):
    base_url: str = "https://api.fantasycalc.com"

    class Config:
        env_prefix = "FANTASY_CALC_"