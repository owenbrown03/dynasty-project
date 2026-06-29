from pydantic import BaseModel


class KTCConfig(BaseModel):
    base_url: str = "https://keeptradecut.com"
    dynasty_path: str = "/dynasty-rankings"
    redraft_path: str = "/fantasy-rankings"
    pages: int = 10
    request_delay: float = 0.5   # seconds between page requests
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
