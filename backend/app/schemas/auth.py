from pydantic import EmailStr, Field

from app.schemas.base import Base

class Login(Base):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)