from typing import Literal

from pydantic import BaseModel

from app.models.menu import MenuCategory


class SearchParams(BaseModel):
    keyword: str | None = None
    category: MenuCategory | None = None
    max_price: float | None = None
    min_discount: float | None = None
    sort_by: Literal["discount", "price_asc", "price_desc", "newest"] = "newest"
    
class MerchantSearchResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    address: str | None = None
    is_active: bool
    available_menu_count: int
    
    class Config:
        from_attributes = True
    
class MenuSearchResponse(BaseModel):
    id: int
    merchant_id: int
    merchant_name: str
    merchant_logo: str | None = None
    title: str
    description: str | None = None
    image_url: str | None = None
    category: str
    original_price: float
    discounted_price: float
    discount_percentage: float | None = None
    quantity: int
    
    class Config:
        from_attributes: True

class SearchResponse(BaseModel):
    merchants: list[MerchantSearchResponse] = []
    menus: list[MenuSearchResponse] = []
    total_merchants: int = 0
    total_menus: int = 0