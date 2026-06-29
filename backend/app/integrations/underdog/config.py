from pydantic import BaseModel


class UnderdogConfig(BaseModel):
    stats_base_url: str = "https://stats.underdogfantasy.com/v1"
    api_base_url: str = "https://api.underdogfantasy.com/v1"
    auth_url: str = "https://login.underdogsports.com/oauth/token"
    client_id: str = "cQvYz1T2BAFbix4dYR37dyD9O0Thf1s6"

    # These are baked into the Underdog JS bundle — update if they 404
    product: str = "fantasy"
    product_experience_id: str = "018e1234-5678-9abc-def0-123456789007"
    state_config_id: str = "16fa6ed3-ea21-4654-bcee-fb32d2f31357"

    @property
    def default_params(self) -> dict:
        return {
            "product": self.product,
            "product_experience_id": self.product_experience_id,
            "state_config_id": self.state_config_id,
        }
