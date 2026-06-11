from app.core.config import settings


class SleeperConfig:
    def __init__(self):
        self.rest_base = settings.SLEEPER_REST_BASE
        self.graphql_url = settings.SLEEPER_GRAPHQL_URL