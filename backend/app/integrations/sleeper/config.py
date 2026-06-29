from app.core.config import settings


class SleeperConfig:
    def __init__(self):
        self.rest_base = settings.SLEEPER_REST_BASE
        self.rest_alt = settings.SLEEPER_REST_ALT
        self.graphql_url = settings.SLEEPER_GRAPHQL_URL

        self.rate_limit_capacity = 10
        self.rate_limit_refill = 10