from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    image : str | None = None
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
class UserLogin(BaseModel):
    email: str
    password: str
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password maksimal 72 karakter")
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v

class ChangeEmail(BaseModel):
    new_email: EmailStr