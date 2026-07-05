# app/schemas/menu.py
from csv import Error

from fastapi import HTTPException
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import datetime
from app.models.menu import MenuCategory, MenuStatus
import decimal

class MenuCreate(BaseModel):
    title: str
    description: str | None = None
    category: MenuCategory = MenuCategory.FOOD
    original_price: decimal.Decimal
    discounted_price: decimal.Decimal
    quantity: int
    max_order_per_user: int | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    image_url: str | None = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_prices(self):
        if self.discounted_price >= self.original_price:
            raise ValueError("Discounted price must be lower than original price")
        if self.discounted_price < 0:
            raise ValueError("Discounted price cannot be negative")
        return self

class MenuUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: MenuCategory | None = None
    original_price: decimal.Decimal | None = None
    discounted_price: decimal.Decimal | None = None
    quantity: int | None = None
    max_order_per_user: int | None = None
    status: MenuStatus | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None
    
class StockUpdate(BaseModel):
    quantity: int
    
    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v
    
class PeriodUpdate(BaseModel):
    available_from: datetime | None = None
    available_until: datetime | None = None
    
    @model_validator(mode="after")
    def validate_period(self):
        if self.available_from and self.available_until:
            if self.available_from >= self.available_until:
                raise ValueError("Waktu Tersedia Sale tidak boleh melebihi Waktu Berakhir Sale")
        return self
    
class MenuResponse(BaseModel):
    id: int
    merchant_id: int
    title: str
    description: str | None = None
    image_url: str | None = None
    category: MenuCategory
    original_price: decimal.Decimal
    discounted_price: decimal.Decimal
    discount_percentage: decimal.Decimal | None = None
    quantity: int
    max_order_per_user: int | None = None
    status: MenuStatus
    is_active: bool
    available_from: datetime | None = None
    available_until: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
        
class BulkDeleteMenu(BaseModel):
    menu_ids: list[int]
    
    @field_validator("menu_ids")
    @classmethod
    def validate_menu_ids(cls, v):
        if len(v) == 0:
            raise ValueError("menu_ids cannot be empty")
        if len(v) > 50:
            raise ValueError("Cannot delete more than 50 menus at once")
        return v