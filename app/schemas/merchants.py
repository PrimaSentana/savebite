from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.menu import MenuResponse


class MerchantCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str
    address: str
    description: str | None = None
    latitude: float
    longitude: float
    is_active: bool = True
    
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
    average_rating: float | None = None
    review_count: int = 0

    class Config:
        from_attributes = True

class MerchantDetailResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    email: str
    phone: str
    logo_url: str | None = None
    banner_url: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool
    is_open: bool
    menus: list[MenuResponse] = []

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
    
class ChangeMerchantPassword(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password max 72 characters")
        if len(v) < 8:
            raise ValueError("Password min 8 characters")
        return v

class ChangeMerchantEmail(BaseModel):
    new_email: EmailStr
    
class NearbyMerchantResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_meters: float
    distance_text: str
    is_active: bool
    available_menu_count: int
    
    class Config:
        from_attributes = True