from pydantic import BaseModel, EmailStr, field_validator


class MerchantCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str
    address: str
    description: str | None = None
    latitude: float
    longitude: float
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password Maksimal 72 Karakter")
        if len(v) < 8:
            raise ValueError("Password Minimal 8 Karakter")
        return v

class MerchantLogin(BaseModel):
    email: str
    password: str

class MerchantResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: str
    address: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool
    is_open: bool

    class Config:
        from_attributes = True

class MerchantResponceImage(BaseModel):
    id: int
    email: str
    name: str
    logo_url: str | None = None
    banner_url: str | None = None

class MerchantUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    description: str | None = None
    is_open: bool | None = None