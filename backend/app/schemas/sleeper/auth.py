from app.schemas.base import Base

class SendCodeRequest(Base):
    username: str
    captcha: str

class VerifyCodeRequest(Base):
    username: str
    code: str
    captcha: str