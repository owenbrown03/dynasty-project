from typing import Optional

from app.schemas.base import Base

class SendCodeRequest(Base):
    username: str
    captcha: str

class SendCodeResponse(Base):
    connect_id: str

class VerifyCodeRequest(Base):
    connect_id: str
    code: str
    captcha: str | None = None

class VerifyCodeResponse(Base):
    sleeper_token: str