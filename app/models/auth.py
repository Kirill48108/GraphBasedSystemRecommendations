from datetime import datetime

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenData(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    role: str = Field(default="user", description="Роль пользователя")


class UserInDB(BaseModel):
    user_id: str
    username: str
    hashed_password: str
    role: str = "user"
    created_at: datetime
