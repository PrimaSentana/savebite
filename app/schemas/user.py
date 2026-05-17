from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    
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